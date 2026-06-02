import re
from typing import List, Set, Tuple

from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.solution_view import DefaultAlertView, SolutionView

class GetSolutionViewUseCase:
    def __init__(
        self,
        alert_repository: AlertRepositoryPort,
        default_alert_repository: DefaultAlertRepositoryPort,
    ):
        self.alert_repository = alert_repository
        self.default_alert_repository = default_alert_repository

    def execute(self, solution: str) -> SolutionView:
        alerts = self.alert_repository.get_all(AlertFilter(solution=solution))
        channels = sorted({a.notification_channel for a in alerts if a.notification_channel})
        micros = {a.microservice for a in alerts if a.microservice}
        default_alerts = [
            _to_default_view(d, solution, micros)
            for d in self.default_alert_repository.get_all()
        ]

        return SolutionView(
            app=solution,
            default_alerts=default_alerts,
            adhoc_alerts=alerts,
            channels=channels,
        )


def _to_default_view(default_alert: DefaultAlert, solution: str, micros: Set[str]) -> DefaultAlertView:
    is_disabled, is_partial, chips = _evaluate(default_alert, solution, micros)
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


def _evaluate(default_alert: DefaultAlert, solution: str, micros: Set[str]) -> Tuple[bool, bool, List[str]]:
    ns_fully_excluded = False
    ns_re_included = False
    partially_excluded = False
    excluded_items: List[str] = []

    targets = {solution} | micros

    for alt in default_alert.excluded_namespaces:
        matched_target = False
        for target in targets:
            if _regex_matches(target, alt):
                ns_fully_excluded = True
                matched_target = True
            elif _is_prefix_of(target, alt):
                partially_excluded = True
                matched_target = True
        if matched_target:
            _append_unique(excluded_items, _display_pattern(alt))

    for incl in default_alert.included_namespaces:
        for target in targets:
            if _regex_matches(target, incl):
                ns_re_included = True
                break

    excluded_items = [
        item for item in excluded_items
        if not any(_regex_matches(item, incl) for incl in default_alert.included_namespaces)
    ]

    for alt in default_alert.excluded_jobs:
        matched_target = False
        for target in targets:
            if _is_prefix_of(target, alt):
                partially_excluded = True
                matched_target = True
                break
        if matched_target:
            _append_unique(excluded_items, _display_pattern(alt))

    is_disabled = ns_fully_excluded and not ns_re_included
    is_partial = partially_excluded and not is_disabled
    if is_disabled:
        excluded_items = []
    return is_disabled, is_partial, excluded_items


def _append_unique(items: List[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _display_pattern(alternative: str) -> str:
    cleaned = alternative.strip()
    for suffix in (".*", ".+"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    return cleaned.rstrip("-").strip() or alternative


def _regex_matches(value: str, pattern: str) -> bool:
    try:
        return re.fullmatch(f"(?:{pattern})", value, re.IGNORECASE) is not None
    except re.error:
        return False


def _literal_prefix(alternative: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(alternative):
        ch = alternative[i]
        if ch == "\\" and i + 1 < len(alternative):
            out.append(alternative[i + 1])
            i += 2
            continue
        if ch in ".*+?()[]{}|^$":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _is_prefix_of(target: str, alternative: str) -> bool:
    if not target:
        return False
    lit = _literal_prefix(alternative).lower()
    prefix = f"{target.lower()}-"
    return lit.startswith(prefix)
