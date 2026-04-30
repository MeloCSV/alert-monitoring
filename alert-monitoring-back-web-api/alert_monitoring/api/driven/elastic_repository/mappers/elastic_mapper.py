import logging
from typing import List, Optional
from alert_monitoring.api.driven.elastic_repository.models.elastic_model import ElasticRule
from alert_monitoring.api.domain.models.alert import Alert

logger = logging.getLogger(__name__)

class ElasticMapper:

    def to_domain(self, rules: List[ElasticRule]) -> List[Alert]:
        return [self._map_rule(rule) for rule in rules]

    def _map_rule(self, rule: ElasticRule) -> Alert:
        confidence = self._calculate_confidence(rule)

        return Alert(
            name=rule.name,
            description=rule.description or "Sin descripción",
            source_tool="Elastic",
            severity=rule.severity or "unknown",
            condition=rule.condition,
            environments=[rule.environment] if rule.environment else [],
            microservice=rule.microservice,
            solution=None,
            notification_channel=rule.canal,
            confidence_level=round(confidence, 2)
        )

    def _calculate_confidence(self, rule: ElasticRule) -> float:
        confidence = 0.0

        if rule.severity:
            confidence += 0.3
        if rule.canal:
            confidence += 0.2
        if rule.microservice:
            confidence += 0.2
        if rule.description:
            confidence += 0.2
        if rule.environment:
            confidence += 0.1

        return confidence