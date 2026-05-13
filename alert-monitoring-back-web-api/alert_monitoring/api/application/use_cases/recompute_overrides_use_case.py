import re
from collections import defaultdict
from typing import List, Optional

from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_override import AlertOverride


_NAMESPACE_LABEL_KEYS = ("namespace", "backend_target_name", "backend_name")


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

    @classmethod
    def _rule_applies(cls, alert: Alert, microservice: str) -> bool:
        excluded = cls._extract_namespace_pattern(alert.condition, exclude=True)
        included = cls._extract_namespace_pattern(alert.condition, exclude=False)
        if not excluded and not included:
            return True
        if included and not _matches_pattern(microservice, included):
            return False
        if excluded and _matches_pattern(microservice, excluded):
            return False
        return True

    @staticmethod
    def _extract_namespace_pattern(expr: Optional[str], exclude: bool) -> Optional[str]:
        if not expr:
            return None
        operator = "!~" if exclude else "=~"
        patterns: list[str] = []
        for key in _NAMESPACE_LABEL_KEYS:
            regex = rf'{key}\s*{re.escape(operator)}\s*"([^"]+)"'
            for match in re.findall(regex, expr):
                if match not in patterns:
                    patterns.append(match)
        if not patterns:
            return None
        return "|".join(patterns)


def _matches_pattern(value: str, pattern: Optional[str]) -> bool:
    if not pattern:
        return False
    try:
        return re.fullmatch(f"(?:{pattern})", value) is not None
    except re.error:
        return False
