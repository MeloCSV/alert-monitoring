import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from alert_monitoring.api.domain.models.kibana_rule import KibanaRule
from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig

logger = logging.getLogger(__name__)


_API_FROM_KQL = re.compile(
    r"transactionElement\.serviceName\s*:\s*\"?([A-Za-z0-9_\-]+)\"?",
    re.IGNORECASE,
)
_CONNECTOR_DISPLAY: Dict[str, str] = {
    ".webhook": "Webhook",
    ".index": "Elastic Index",
    ".teams": "Microsoft Teams",
    ".slack": "Slack",
    ".email": "Email",
    ".pagerduty": "PagerDuty",
    ".server-log": "Server Log",
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

        apis = self._extract_apis(params)
        is_global = self._is_global(raw, tags, apis)

        return KibanaRule(
            rule_id=str(raw.get("id") or ""),
            name=str(raw.get("name") or ""),
            enabled=bool(raw.get("enabled", False)),
            tags=tags,
            schedule_interval=(raw.get("schedule") or {}).get("interval"),
            severity=self._infer_severity(actions),
            notification_channels=self._infer_channels(actions),
            apis=apis,
            is_global=is_global,
            last_execution_date=(raw.get("execution_status") or {}).get("last_execution_date"),
            last_execution_status=(raw.get("execution_status") or {}).get("status"),
            kibana_url=self._build_rule_url(raw.get("id"), config),
            kibana_name=config.name,
            message=self._extract_message(actions),
        )

    def _extract_apis(self, params: dict) -> List[str]:
        apis: List[str] = []

        search_config = params.get("searchConfiguration") or {}
        kql = (search_config.get("query") or {}).get("query") or ""
        for match in _API_FROM_KQL.finditer(kql):
            value = match.group(1).strip()
            if value and value not in apis:
                apis.append(value)

        return apis

    def _is_global(self, raw: dict, tags: List[str], apis: List[str]) -> bool:
        return not apis

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

            # .index connector: documents[0].alerts[0].annotations.message
            # or documents[0].message (direct)
            if connector == ".index":
                for doc in params.get("documents") or []:
                    for alert in doc.get("alerts") or []:
                        msg = (alert.get("annotations") or {}).get("message")
                        if msg:
                            return str(msg)
                    msg = doc.get("message")
                    if msg:
                        return str(msg)

            # .webhook connector: body is a JSON string → [0].annotations.message
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
        channels: List[str] = []
        for action in actions:
            connector = action.get("connector_type_id") or ""
            display = _CONNECTOR_DISPLAY.get(connector, connector.lstrip(".").capitalize() if connector else None)
            if display and display not in channels:
                channels.append(display)
        return channels

    def _build_rule_url(self, rule_id: Optional[str], config: KibanaConfig) -> Optional[str]:
        if not rule_id:
            return None
        base = config.base_url.rstrip("/")
        if config.space_id:
            base = f"{base}/s/{config.space_id}"
        return f"{base}/app/management/insightsAndAlerting/triggersActions/rule/{rule_id}"
