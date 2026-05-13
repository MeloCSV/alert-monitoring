import re
from collections import defaultdict
from typing import List, Optional

from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_override import AlertOverride


class RecomputeOverridesUseCase:
    def __init__(self, alert_repository: AlertRepositoryPort, override_repository: AlertOverrideRepositoryPort):
        self.alert_repository = alert_repository
        self.override_repository = override_repository

    def execute(self) -> int:
        alerts = self.alert_repository.get_all()
        default_alerts = [a for a in alerts if a.alert_type == "Por Defecto"]
        microservices = sorted({
            a.microservice for a in alerts
            if a.alert_type == "Ad-hoc" and a.microservice
        })

        buckets: dict[str, List[Alert]] = defaultdict(list)
        for alert in default_alerts:
            buckets[alert.name].append(alert)

        overrides: List[AlertOverride] = []
        for name, bucket in buckets.items():
            for micro in microservices:
                applies = any(self._rule_applies(rule, micro) for rule in bucket)
                overrides.append(AlertOverride(
                    alert_name=name,
                    microservice=micro,
                    is_disabled=not applies,
                ))

        self.override_repository.replace_all(overrides)
        return len(overrides)

    @staticmethod
    def _rule_applies(alert: Alert, microservice: str) -> bool:
        has_include = bool(alert.included_namespaces)
        has_exclude = bool(alert.excluded_namespaces)
        if not has_include and not has_exclude:
            return True
        if has_include and not _matches_pattern(microservice, alert.included_namespaces):
            return False
        if has_exclude and _matches_pattern(microservice, alert.excluded_namespaces):
            return False
        return True


def _matches_pattern(value: str, pattern: Optional[str]) -> bool:
    if not pattern:
        return False
    try:
        return re.fullmatch(f"(?:{pattern})", value) is not None
    except re.error:
        return False
