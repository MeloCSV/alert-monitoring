import logging
from typing import List, Optional

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.driven.elastic_repository.models.elastic_model import ElasticRule
from alert_monitoring.api.driven.shared.alert_normalization import (
    display_canal,
    environments_or_all,
    resolve_channels_from_labels,
)

logger = logging.getLogger(__name__)


class ElasticMapper:

    def to_domain(self, rules: List[ElasticRule]) -> List[Alert]:
        return [self._map_rule(rule) for rule in rules]

    def _map_rule(self, rule: ElasticRule) -> Alert:
        labels = rule.labels
        return Alert(
            name=rule.name,
            description=rule.description or "Sin descripción",
            source_tool="Elastic",
            severity=labels.get("severity") or "unknown",
            environments=environments_or_all(rule.environments),
            microservice=self._infer_microservice(rule),
            solution=labels.get("application"),
            notification_channel=self._infer_channel(rule),
        )

    def _infer_channel(self, rule: ElasticRule) -> Optional[str]:
        destinations: List[str] = []
        for canal in rule.canals:
            if canal.lower() == "alertmanager":
                for dest in resolve_channels_from_labels(rule.labels):
                    if dest not in destinations:
                        destinations.append(dest)
                if not resolve_channels_from_labels(rule.labels):
                    display = display_canal(canal)
                    if display and display not in destinations:
                        destinations.append(display)
            else:
                display = display_canal(canal)
                if display and display not in destinations:
                    destinations.append(display)

        if not destinations:
            for dest in resolve_channels_from_labels(rule.labels):
                if dest not in destinations:
                    destinations.append(dest)

        return " / ".join(destinations) if destinations else None

    def _infer_microservice(self, rule: ElasticRule) -> Optional[str]:
        labels = rule.labels
        for key in ("application", "deployment", "service", "namespace", "pod", "job"):
            value = labels.get(key)
            if value:
                return value
        return None
