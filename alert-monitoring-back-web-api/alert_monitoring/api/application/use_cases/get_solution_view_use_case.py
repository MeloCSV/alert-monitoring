from typing import List, Optional

from alert_monitoring.api.application.ports.driven.alert_disabled_repository_port import AlertDisabledRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.alert_disabled import AlertDisabled
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.solution_view import DefaultAlertView, SolutionView
from alert_monitoring.api.driven.shared.alert_normalization import extract_adhoc_chips


class GetSolutionViewUseCase:
    def __init__(
        self,
        alert_repository: AlertRepositoryPort,
        disabled_repository: AlertDisabledRepositoryPort,
        default_alert_repository: DefaultAlertRepositoryPort,
    ):
        self.alert_repository = alert_repository
        self.disabled_repository = disabled_repository
        self.default_alert_repository = default_alert_repository

    def execute(self, solution: str) -> SolutionView:
        alerts = [
            a for a in self.alert_repository.get_all(AlertFilter(solution=solution))
            if a.solution == solution
        ]
        channels = sorted({a.notification_channel for a in alerts if a.notification_channel})

        for alert in alerts:
            alert.chips = extract_adhoc_chips(alert.condition)

        disabled_map = {o.alert_name: o for o in self.disabled_repository.get_all(solution)}
        default_alerts = [
            v for d in self.default_alert_repository.get_all()
            for v in [_to_default_view(d, disabled_map.get(d.raw_name))]
            if not v.is_disabled
        ]

        return SolutionView(
            solution=solution,
            default_alerts=default_alerts,
            adhoc_alerts=alerts,
            channels=channels,
        )


def _to_default_view(default_alert: DefaultAlert, alert_disabled: Optional[AlertDisabled]) -> DefaultAlertView:
    is_disabled = bool(alert_disabled and alert_disabled.is_disabled)
    is_partial = bool(alert_disabled and not alert_disabled.is_disabled and alert_disabled.is_partial)
    chips = [] if not alert_disabled or alert_disabled.is_disabled else alert_disabled.excluded_items
    return DefaultAlertView(
        raw_name=default_alert.raw_name,
        name=default_alert.display_name,
        description=default_alert.display_description or default_alert.raw_description,
        severity=default_alert.severity,
        notification_channel=default_alert.notification_channel,
        environments=["pro"],
        is_disabled=is_disabled,
        is_partial=is_partial,
        chips=chips,
    )
