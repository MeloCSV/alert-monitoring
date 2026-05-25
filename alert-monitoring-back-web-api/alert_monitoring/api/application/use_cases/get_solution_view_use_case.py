import re
from typing import List, Optional

from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.alert_override import AlertOverride
from alert_monitoring.api.domain.models.blackout import Blackout
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.solution_view import DefaultAlertView, SolutionView
from alert_monitoring.api.driven.shared.alert_normalization import extract_adhoc_chips

# Etiquetas de matcher de AlertManager que asocian un silencio a una aplicación.
APP_MATCHER_FIELDS = frozenset({
    "namespace", "solucion", "solution", "exported_namespace",
    "backend_target_name", "deployment", "replicaset", "cronjob", "pod",
})


class GetSolutionViewUseCase:
    def __init__(
        self,
        alert_repository: AlertRepositoryPort,
        override_repository: AlertOverrideRepositoryPort,
        default_alert_repository: DefaultAlertRepositoryPort,
    ):
        self.alert_repository = alert_repository
        self.override_repository = override_repository
        self.default_alert_repository = default_alert_repository

    def execute(self, solution: str, blackouts: List[Blackout]) -> SolutionView:
        alerts = [
            a for a in self.alert_repository.get_all(AlertFilter(solution=solution))
            if a.solution == solution
        ]
        channels = sorted({a.notification_channel for a in alerts if a.notification_channel})

        adhoc_alerts = [a for a in alerts if a.alert_type == "Ad-hoc"]
        for alert in adhoc_alerts:
            alert.chips = extract_adhoc_chips(alert.condition)

        overrides = {o.alert_name: o for o in self.override_repository.get_all(solution)}
        default_alerts = [
            _to_default_view(d, overrides.get(d.raw_name))
            for d in self.default_alert_repository.get_all()
        ]

        solution_blackouts = [b for b in blackouts if _blackout_matches(b, solution)]

        return SolutionView(
            solution=solution,
            default_alerts=default_alerts,
            adhoc_alerts=adhoc_alerts,
            blackouts=solution_blackouts,
            channels=channels,
        )


def _to_default_view(default_alert: DefaultAlert, override: Optional[AlertOverride]) -> DefaultAlertView:
    is_overridden = bool(override and override.is_disabled)
    is_partial = bool(override and not override.is_disabled and override.is_partial)
    chips = [] if not override or override.is_disabled else override.excluded_items
    return DefaultAlertView(
        raw_name=default_alert.raw_name,
        name=default_alert.display_name,
        description=default_alert.display_description,
        severity=default_alert.severity,
        notification_channel=default_alert.notification_channel,
        environments=["pro"],
        is_overridden=is_overridden,
        is_partial=is_partial,
        chips=chips,
    )


def _blackout_matches(blackout: Blackout, solution: str) -> bool:
    sol = solution.lower()
    variants = (sol, f"{sol}-back", f"{sol}-front")
    return any(_matcher_matches(m.name, m.value, m.is_regex, m.is_equal, variants) for m in blackout.matchers)


def _matcher_matches(name: str, value: str, is_regex: bool, is_equal: bool, variants) -> bool:
    if name not in APP_MATCHER_FIELDS or not is_equal:
        return False
    if is_regex:
        try:
            return any(re.search(value, v) is not None for v in variants)
        except re.error:
            return False
    val = value.lower()
    return any(val == v or val.startswith(f"{v}-") for v in variants)
