import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi
from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig
from alert_monitoring.api.driven.shared.alert_normalization import DEFAULT_ALERT_DISPLAY

logger = logging.getLogger(__name__)

# API-monitoring KQL patterns
_SERVICE_NAME_CLAUSE = re.compile(
    r"(?P<neg>\bNOT\s+)?transactionElement\.serviceName\s*:\s*(?P<val>\([^)]+\)|\"[^\"]+\"|[A-Za-z0-9_\-]+)",
    re.IGNORECASE,
)
_API_CLAUSE = re.compile(
    r"(?P<neg>\bNOT\s+)?(?<!\w)api\s*:\s*(?P<val>\"[^\"]+\"|[A-Za-z0-9_\-]+)",
    re.IGNORECASE,
)
_QUOTED_VALUE = re.compile(r'"([A-Za-z0-9_\-]+)"')

# Log-based rules patterns
_KQL_APPLICATION = re.compile(
    r'(?<!\w)application\s*:\s*(?:"([^"]+)"|([A-Za-z0-9_.\-]+))',
    re.IGNORECASE,
)
_KQL_NAMESPACE = re.compile(
    r'k8s\.namespace\.name\s*:\s*(?:"([^"]+)"|([A-Za-z0-9_\-]+))',
    re.IGNORECASE,
)
_KQL_DEPLOYMENT = re.compile(
    r'k8s\.deployment\.name\s*:\s*(?:"([^"]+)"|([A-Za-z0-9_\-]+))',
    re.IGNORECASE,
)
_INDEX_APP = re.compile(
    r'logs[-_]otel[-_]([a-z][a-z0-9\-]+?)(?:[-_]gke[-_]|[-_]\*|[-_]pro|\*)',
    re.IGNORECASE,
)

_INTERNAL_CONNECTORS = {".server-log"}

# canal field in .index documents → display channel name
_INDEX_CANAL_CHANNELS: Dict[str, str] = {
    "alertmanager": "AlertManager",
    "teams": "Microsoft Teams",
    "msteams": "Microsoft Teams",
    "omi": "ServiceNow",
    "itom": "ServiceNow",
    "jira": "Jira",
    "mail": "Email",
}

_WEBHOOK_LABEL_CHANNELS: Dict[str, str] = {
    "msteams": "Microsoft Teams",
    "omi": "ServiceNow",
}

_CONNECTOR_DISPLAY: Dict[str, str] = {
    ".teams": "Microsoft Teams",
    ".slack": "Slack",
    ".email": "Email",
    ".pagerduty": "PagerDuty",
}

# Lower value = higher priority
_CHANNEL_PRIORITY: Dict[str, int] = {
    "ServiceNow": 0,
    "AlertManager": 1,
    "Microsoft Teams": 2,
    "Jira": 3,
    "Email": 4,
    "Slack": 5,
    "PagerDuty": 6,
}

_TEMPLATE_PREFIX = "{{"


class KibanaRuleMapper:

    def to_domain(self, rules: List[dict], config: KibanaConfig) -> List[AlertApi]:
        _, adhoc = self.to_domain_split(rules, config)
        return adhoc

    def to_domain_split(
        self, rules: List[dict], config: KibanaConfig
    ) -> Tuple[List[DefaultAlertApi], List[AlertApi]]:
        defaults: List[DefaultAlertApi] = []
        adhoc: List[AlertApi] = []
        for raw in rules:
            try:
                raw_name = str(raw.get("name") or "")
                if re.match(r"^\[global\]", raw_name, re.IGNORECASE):
                    if bool(raw.get("enabled", True)):
                        defaults.append(self._map_global_rule(raw, config))
                else:
                    if bool(raw.get("enabled", False)):
                        adhoc.append(self._map_adhoc_rule(raw, config))
            except Exception as exc:
                logger.warning("Error mapeando regla Kibana '%s': %s", raw.get("name", "?"), exc)
        return defaults, adhoc

    def _map_global_rule(self, raw: dict, config: KibanaConfig) -> DefaultAlertApi:
        actions = raw.get("actions") or []
        params = raw.get("params") or {}
        raw_name = str(raw.get("name") or "")
        stripped_name = re.sub(r"^\[global\]\s*", "", raw_name, flags=re.IGNORECASE)
        _, excluded_apis = self._extract_apis_split(params)
        display = DEFAULT_ALERT_DISPLAY.get(stripped_name)
        return DefaultAlertApi(
            raw_name=stripped_name,
            display_name=display[0] if display else stripped_name,
            raw_description=self._extract_message(actions),
            display_description=display[1] if display else None,
            severity=self._infer_severity(actions),
            notification_channel=self._infer_channel(actions),
            excluded_apis=excluded_apis,
        )

    def _map_adhoc_rule(self, raw: dict, config: KibanaConfig) -> AlertApi:
        actions = raw.get("actions") or []
        params = raw.get("params") or {}
        positive_apis, _ = self._extract_apis_split(params)
        return AlertApi(
            rule_id=str(raw.get("id") or ""),
            name=str(raw.get("name") or ""),
            severity=self._infer_severity(actions),
            notification_channel=self._infer_channel(actions),
            apis_alertadas=positive_apis,
            message=self._extract_message(actions),
            application=self._extract_application(actions, params),
            microservice=self._extract_microservice(params),
        )

    # ── API extraction (existing logic) ─────────────────────────────────────

    def _extract_apis_split(self, params: dict) -> Tuple[List[str], List[str]]:
        """Returns (positive_apis, negated_apis) parsed from the KQL."""
        search_config = params.get("searchConfiguration") or {}
        kql = (search_config.get("query") or {}).get("query") or ""

        positive: set = set()
        negated: set = set()

        for m in _SERVICE_NAME_CLAUSE.finditer(kql):
            is_negated = bool(m.group("neg"))
            clause = m.group("val")
            values = self._parse_clause_values(clause)
            for v in values:
                if v:
                    (negated if is_negated else positive).add(v)

        for m in _API_CLAUSE.finditer(kql):
            is_negated = bool(m.group("neg"))
            clause = m.group("val")
            values = self._parse_clause_values(clause)
            for v in values:
                if v:
                    (negated if is_negated else positive).add(v)

        return sorted(positive - negated), sorted(negated)

    def _extract_apis(self, params: dict) -> List[str]:
        positive, _ = self._extract_apis_split(params)
        return positive

    def _parse_clause_values(self, clause: str) -> List[str]:
        if clause.startswith("("):
            return [qm.group(1) for qm in _QUOTED_VALUE.finditer(clause)]
        if clause.startswith('"'):
            return [clause.strip('"')]
        return [clause.strip()]

    # ── Severity ─────────────────────────────────────────────────────────────

    def _infer_severity(self, actions: List[dict]) -> Optional[str]:
        for action in actions:
            params = action.get("params") or {}
            for doc in params.get("documents") or []:
                severity = self._severity_from_doc(doc)
                if severity:
                    return severity
            body = params.get("body")
            if isinstance(body, str):
                severity = self._severity_from_body(body)
                if severity:
                    return severity
        return None

    def _severity_from_doc(self, doc: dict) -> Optional[str]:
        # alertManagerBody.labels.severity
        sev = ((doc.get("alertManagerBody") or {}).get("labels") or {}).get("severity")
        if sev:
            return str(sev).capitalize()
        # direct severity field
        sev = doc.get("severity")
        if sev:
            return str(sev).capitalize()
        # level field
        level = doc.get("level")
        if level:
            return str(level).capitalize()
        # legacy: alerts array
        for alert in doc.get("alerts") or []:
            sev = (alert.get("labels") or {}).get("severity")
            if sev:
                return str(sev).capitalize()
        return None

    def _severity_from_body(self, body: str) -> Optional[str]:
        match = re.search(r'"severity"\s*:\s*"([^"]+)"', body)
        if match:
            return match.group(1).capitalize()
        return None

    # ── Message ──────────────────────────────────────────────────────────────

    def _extract_message(self, actions: List[dict]) -> Optional[str]:
        for action in actions:
            params = action.get("params") or {}
            connector = action.get("connector_type_id") or ""

            if connector == ".index":
                for doc in params.get("documents") or []:
                    msg = ((doc.get("alertManagerBody") or {}).get("annotations") or {}).get("message")
                    if msg:
                        return str(msg)
                    msg = doc.get("message")
                    if msg:
                        return str(msg)

            elif connector == ".webhook":
                body = params.get("body")
                if isinstance(body, str):
                    try:
                        parsed = json.loads(body)
                        if isinstance(parsed, list) and parsed:
                            msg = (parsed[0].get("annotations") or {}).get("message")
                            if msg:
                                return str(msg)
                    except (json.JSONDecodeError, AttributeError):
                        pass

        return None

    # ── Notification channel ─────────────────────────────────────────────────

    def _infer_channel(self, actions: List[dict]) -> Optional[str]:
        channels: List[str] = []

        for action in actions:
            connector = action.get("connector_type_id") or ""
            params = action.get("params") or {}

            if connector == ".index":
                for doc in params.get("documents") or []:
                    canal = str(doc.get("canal") or "").lower()
                    display = _INDEX_CANAL_CHANNELS.get(canal)
                    if display and display not in channels:
                        channels.append(display)
                continue

            if connector in _INTERNAL_CONNECTORS:
                continue

            if connector == ".webhook":
                channel = self._channel_from_webhook_body(action)
                if channel and channel not in channels:
                    channels.append(channel)
                continue

            display = _CONNECTOR_DISPLAY.get(connector)
            if not display and connector:
                display = connector.lstrip(".").capitalize()
            if display and display not in channels:
                channels.append(display)

        if not channels:
            return None
        return min(channels, key=lambda ch: _CHANNEL_PRIORITY.get(ch, 99))

    def _channel_from_webhook_body(self, action: dict) -> Optional[str]:
        body = (action.get("params") or {}).get("body")
        if not isinstance(body, str):
            return None
        try:
            parsed = json.loads(body)
            labels: dict = {}
            if isinstance(parsed, list) and parsed:
                labels = parsed[0].get("labels") or {}
            elif isinstance(parsed, dict):
                labels = parsed.get("labels") or {}
            for label_key, display_name in _WEBHOOK_LABEL_CHANNELS.items():
                if str(labels.get(label_key, "")).lower() == "true":
                    return display_name
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
        return None

    # ── Application ──────────────────────────────────────────────────────────

    def _extract_application(self, actions: List[dict], params: dict) -> Optional[str]:
        # 1. alertManagerBody.labels.application (skip Mustache template values)
        for action in actions:
            if (action.get("connector_type_id") or "") != ".index":
                continue
            for doc in (action.get("params") or {}).get("documents") or []:
                app = ((doc.get("alertManagerBody") or {}).get("labels") or {}).get("application")
                if app and not str(app).startswith(_TEMPLATE_PREFIX):
                    return str(app)

        # 2. KQL application: field
        kql = self._get_kql(params)
        if kql:
            m = _KQL_APPLICATION.search(kql)
            if m:
                return str(m.group(1) or m.group(2))

        # 3. KQL k8s.namespace.name
        if kql:
            m = _KQL_NAMESPACE.search(kql)
            if m:
                return str(m.group(1) or m.group(2))

        # 4. esQuery JSON must clause k8s.namespace.name
        es_query_str = params.get("esQuery") or ""
        if es_query_str:
            try:
                ns = self._find_must_value(
                    json.loads(es_query_str).get("query") or {}, "k8s.namespace.name"
                )
                if ns:
                    return ns
            except (json.JSONDecodeError, TypeError):
                pass

        # 5. Index pattern: logs-otel-{app}-*
        return self._app_from_index(params)

    def _extract_microservice(self, params: dict) -> Optional[str]:
        # 1. KQL k8s.deployment.name (positive match, not preceded by NOT)
        kql = self._get_kql(params)
        if kql:
            for m in _KQL_DEPLOYMENT.finditer(kql):
                preceding = kql[max(0, m.start() - 10):m.start()]
                if not re.search(r'\bNOT\b', preceding, re.IGNORECASE):
                    return str(m.group(1) or m.group(2))

        # 2. esQuery JSON must clause k8s.deployment.name
        es_query_str = params.get("esQuery") or ""
        if es_query_str:
            try:
                depl = self._find_must_value(
                    json.loads(es_query_str).get("query") or {}, "k8s.deployment.name"
                )
                if depl:
                    return depl
            except (json.JSONDecodeError, TypeError):
                pass

        return None

    def _get_kql(self, params: dict) -> str:
        search_config = params.get("searchConfiguration") or {}
        return (search_config.get("query") or {}).get("query") or ""

    def _find_must_value(self, query: dict, field: str) -> Optional[str]:
        """Find the positive value of a field in the must clause of a bool query."""
        bool_q = query.get("bool") or {}
        for clause in (bool_q.get("must") or []):
            # term: {"field": {"value": "x"}} or {"field": "x"}
            term = (clause.get("term") or {}).get(field)
            if term is not None:
                val = term.get("value") if isinstance(term, dict) else term
                if val:
                    return str(val)
            # match / match_phrase: {"field": "x"} or {"field": {"query": "x"}}
            for match_type in ("match", "match_phrase"):
                match_val = (clause.get(match_type) or {}).get(field)
                if match_val is not None:
                    if isinstance(match_val, dict):
                        val = match_val.get("query") or match_val.get("value")
                    else:
                        val = match_val
                    if val:
                        return str(val)
        return None

    def _app_from_index(self, params: dict) -> Optional[str]:
        indices = params.get("index") or []
        if isinstance(indices, str):
            indices = [indices]
        for idx in indices:
            if isinstance(idx, dict):
                idx_str = str(idx.get("title") or idx.get("name") or "")
            else:
                idx_str = str(idx)
            m = _INDEX_APP.search(idx_str)
            if m:
                return m.group(1)
        return None
