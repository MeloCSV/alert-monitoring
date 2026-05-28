import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from alert_monitoring.api.domain.models.kibana_rule import KibanaRule
from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig

logger = logging.getLogger(__name__)

# Matches: [NOT] transactionElement.serviceName : value-or-group
_SERVICE_NAME_CLAUSE = re.compile(
    r"(?P<neg>\bNOT\s+)?transactionElement\.serviceName\s*:\s*(?P<val>\([^)]+\)|\"[^\"]+\"|[A-Za-z0-9_\-]+)",
    re.IGNORECASE,
)
# Matches: [NOT] api : value  (simple api field used in non-global rules)
_API_CLAUSE = re.compile(
    r"(?P<neg>\bNOT\s+)?(?<!\w)api\s*:\s*(?P<val>\"[^\"]+\"|[A-Za-z0-9_\-]+)",
    re.IGNORECASE,
)
_QUOTED_VALUE = re.compile(r'"([A-Za-z0-9_\-]+)"')

# Connectors that are purely internal logging – not user-facing channels
_INTERNAL_CONNECTORS = {".index", ".server-log"}

# Webhook body label → display channel name
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


class KibanaRuleMapper:

    def to_domain(self, rules: List[dict], config: KibanaConfig) -> List[KibanaRule]:
        mapped: List[KibanaRule] = []
        for raw in rules:
            try:
                mapped.append(self._map_rule(raw, config))
            except Exception as exc:
                logger.warning("Error mapeando regla Kibana '%s': %s", raw.get("name", "?"), exc)
        return mapped

    def _map_rule(self, raw: dict, config: KibanaConfig) -> KibanaRule:
        actions = raw.get("actions") or []
        params = raw.get("params") or {}
        tags = [str(t) for t in (raw.get("tags") or []) if t]

        apis, disabled_apis = self._extract_apis(params)
        is_global = self._is_global(raw, tags)

        raw_name = str(raw.get("name") or "")
        return KibanaRule(
            rule_id=str(raw.get("id") or ""),
            name=re.sub(r"^\[global\]\s*", "", raw_name, flags=re.IGNORECASE),
            enabled=bool(raw.get("enabled", False)),
            tags=tags,
            schedule_interval=(raw.get("schedule") or {}).get("interval"),
            severity=self._infer_severity(actions),
            notification_channels=self._infer_channels(actions),
            apis=apis,
            disabled_apis=disabled_apis,
            is_global=is_global,
            last_execution_date=(raw.get("execution_status") or {}).get("last_execution_date"),
            last_execution_status=(raw.get("execution_status") or {}).get("status"),
            kibana_url=self._build_rule_url(raw.get("id"), config),
            kibana_name=config.name,
            message=self._extract_message(actions),
        )

    def _extract_apis(self, params: dict) -> Tuple[List[str], List[str]]:
        """Returns (positive_apis, disabled_apis).

        - positive_apis: APIs explicitly included (from 'api :' clauses or positive serviceName)
        - disabled_apis: APIs explicitly excluded (from 'NOT transactionElement.serviceName:')
        """
        search_config = params.get("searchConfiguration") or {}
        kql = (search_config.get("query") or {}).get("query") or ""

        positive: set = set()
        negated: set = set()

        # Global rules use transactionElement.serviceName with NOT to exclude
        for m in _SERVICE_NAME_CLAUSE.finditer(kql):
            is_negated = bool(m.group("neg"))
            clause = m.group("val")
            values = self._parse_clause_values(clause)
            for v in values:
                if v:
                    (negated if is_negated else positive).add(v)

        # Non-global / per-app rules use bare 'api :' field to include
        for m in _API_CLAUSE.finditer(kql):
            is_negated = bool(m.group("neg"))
            clause = m.group("val")
            values = self._parse_clause_values(clause)
            for v in values:
                if v:
                    (negated if is_negated else positive).add(v)

        included = [v for v in positive if v not in negated]
        disabled = sorted(negated)
        return included, disabled

    def _parse_clause_values(self, clause: str) -> List[str]:
        if clause.startswith("("):
            return [qm.group(1) for qm in _QUOTED_VALUE.finditer(clause)]
        if clause.startswith('"'):
            return [clause.strip('"')]
        return [clause.strip()]

    def _is_global(self, raw: dict, tags: List[str]) -> bool:
        return "global" in tags

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
        for alert in doc.get("alerts") or []:
            labels = alert.get("labels") or {}
            sev = labels.get("severity")
            if sev:
                return str(sev).capitalize()
        sev = doc.get("severity")
        if sev:
            return str(sev).capitalize()
        return None

    def _severity_from_body(self, body: str) -> Optional[str]:
        match = re.search(r'"severity"\s*:\s*"([^"]+)"', body)
        if match:
            return match.group(1).capitalize()
        return None

    def _extract_message(self, actions: List[dict]) -> Optional[str]:
        for action in actions:
            params = action.get("params") or {}
            connector = action.get("connector_type_id") or ""

            if connector == ".index":
                for doc in params.get("documents") or []:
                    for alert in doc.get("alerts") or []:
                        msg = (alert.get("annotations") or {}).get("message")
                        if msg:
                            return str(msg)
                    msg = doc.get("message")
                    if msg:
                        return str(msg)

            if connector == ".webhook":
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

    def _infer_channels(self, actions: List[dict]) -> List[str]:
        """Map connector actions to display channel names.

        - .index / .server-log  → internal, skip
        - .teams                → Microsoft Teams
        - .webhook              → inspect body labels for msteams/omi
        - others                → use _CONNECTOR_DISPLAY or capitalize
        """
        channels: List[str] = []

        for action in actions:
            connector = action.get("connector_type_id") or ""

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

        return channels

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

    def _build_rule_url(self, rule_id: Optional[str], config: KibanaConfig) -> Optional[str]:
        if not rule_id:
            return None
        base = config.base_url.rstrip("/")
        if config.space_id:
            base = f"{base}/s/{config.space_id}"
        return f"{base}/app/management/insightsAndAlerting/triggersActions/rule/{rule_id}"
