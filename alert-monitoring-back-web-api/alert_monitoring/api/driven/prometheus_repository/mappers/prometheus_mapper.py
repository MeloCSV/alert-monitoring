import re
import logging
from typing import List, Optional
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule
from alert_monitoring.api.domain.models.alert import Alert

logger = logging.getLogger(__name__)


class PrometheusMapper:
    def to_domain(self, rules: List[PrometheusRule]) -> List[Alert]:
        return [self._map_rule(rule) for rule in rules]

    def _map_rule(self, rule: PrometheusRule) -> Alert:
        labels = rule.labels

        return Alert(
            name=rule.alert,
            description=rule.annotations.get("message", "Sin descripción"),
            source_tool="Prometheus",
            severity=labels.get("severity", "unknown"),
            condition=rule.expr,
            environments=self._label_value(labels, "environment"),
            microservice=self._label_or_none(labels, "namespace"),
            solution=labels.get("solucion") or None,
            notification_channel=labels.get("canal") or None,
            alert_type="Por Defecto" if str(labels.get("alertype", "")).lower() == "default" else "Ad-hoc",
            excluded_namespaces=self._excluded_namespaces(rule.expr),
        )

    def _label_or_none(self, labels: dict, key: str) -> Optional[str]:
        value = labels.get(key)
        if not value or "{{" in str(value):
            return None
        return str(value)

    def _label_value(self, labels: dict, key: str) -> List[str]:
        value = self._label_or_none(labels, key)
        return [value] if value else []

    def _excluded_namespaces(self, expr: str) -> List[str]:
        if not expr:
            return []
        found: List[str] = []
        seen = set()
        for raw in re.findall(r'(?:namespace|exported_namespace)\s*!~\s*"([^"]+)"', expr):
            for part in raw.split("|"):
                cleaned = part.strip()
                if not cleaned or cleaned in seen:
                    continue
                seen.add(cleaned)
                found.append(cleaned)
        return found
