import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from alert_monitoring.api.domain.models.kibana_rule import AlertApi
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

_INTERNAL_CONNECTORS = {".index", ".server-log"}

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

# Lower value = higher priority (most restrictive)
_CHANNEL_PRIORITY: Dict[str, int] = {
    "ServiceNow": 0,
    "Microsoft Teams": 1,
    "Slack": 2,
    "Email": 3,
    "PagerDuty": 4,
}


class KibanaRuleMapper:

    def to_domain(self, rules: List[dict], config: KibanaConfig) -> List[AlertApi]:
        mapped: List[AlertApi] = []
        for raw in rules:
            try:
                mapped.append(self._map_rule(raw, config))
            except Exception as exc:
                logger.warning("Error mapeando regla Kibana '%s': %s", raw.get("name", "?"), exc)
        return mapped

    def _map_rule(self, raw: dict, config: KibanaConfig) -> AlertApi:
        actions = raw.get("actions") or []
        params = raw.get("params") or {}
        tags = [str(t) for t in (raw.get("tags") or []) if t]

        apis_alertadas = self._extract_apis(params)

        raw_name = str(raw.get("name") or "")
        return AlertApi(
            rule_id=str(raw.get("id") or ""),
            name=re.sub(r"^\[global\]\s*", "", raw_name, flags=re.IGNORECASE),
            enabled=bool(raw.get("enabled", False)),
            tags=tags,
            severity=self._infer_severity(actions),
            notification_channel=self._infer_channel(actions),
            apis_alertadas=apis_alertadas,
            message=self._extract_message(actions),
        )

    def _extract_apis(self, params: dict) -> List[str]:
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

        return [v for v in positive if v not in negated]

    def _parse_clause_values(self, clause: str) -> List[str]:
        if clause.startswith("("):
            return [qm.group(1) for qm in _QUOTED_VALUE.finditer(clause)]
        if clause.startswith('"'):
            return [clause.strip('"')]
        return [clause.strip()]

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

    def _infer_channel(self, actions: List[dict]) -> Optional[str]:
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
