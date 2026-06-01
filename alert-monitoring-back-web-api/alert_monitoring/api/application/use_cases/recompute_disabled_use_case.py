from collections import defaultdict
from typing import List, Set, Tuple

from alert_monitoring.api.application.ports.driven.alert_disabled_repository_port import AlertDisabledRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.domain.models.alert_disabled import AlertDisabled
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.driven.shared.alert_normalization import (
    NAMESPACE_LABEL_KEYS,
    JOB_LABEL_KEYS,
    extract_label_alternatives,
)


class RecomputeDisabledUseCase:
    def __init__(
        self,
        alert_repository: AlertRepositoryPort,
        disabled_repository: AlertDisabledRepositoryPort,
        default_alert_repository: DefaultAlertRepositoryPort,
    ):
        self.alert_repository = alert_repository
        self.disabled_repository = disabled_repository
        self.default_alert_repository = default_alert_repository

    def execute(self) -> int:
        alerts = self.alert_repository.get_all()

        # Build solution → set of microservices from Ad-hoc alerts
        solution_micros: dict[str, Set[str]] = defaultdict(set)
        for a in alerts:
            if a.solution and a.solution != "unknown" and a.microservice:
                solution_micros[a.solution].add(a.microservice)

        solutions = sorted(solution_micros.keys())
        default_alerts = self.default_alert_repository.get_all()

        disabled_alerts: List[AlertDisabled] = []
        for default_alert in default_alerts:
            for sol in solutions:
                micros = solution_micros[sol]
                is_disabled, is_partial, excluded_items = _evaluate(default_alert, sol, micros)
                if not (is_disabled or is_partial or excluded_items):
                    continue
                disabled_alerts.append(AlertDisabled(
                    alert_name=default_alert.raw_name,
                    solution=sol,
                    is_disabled=is_disabled,
                    is_partial=is_partial,
                    excluded_items=excluded_items,
                ))

        self.disabled_repository.replace_all(disabled_alerts)
        return len(disabled_alerts)


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


def build_exclusion_updates(default_alert_rules) -> dict:
    """Merge exclusion patterns from all default alert rule instances grouped by raw_name.

    Returns a dict mapping raw_name → (excluded_namespaces, included_namespaces, excluded_jobs).
    """
    buckets: dict[str, dict] = defaultdict(lambda: {"excl_ns": set(), "incl_ns": set(), "excl_jobs": set()})

    for alert in default_alert_rules:
        raw_name = alert.prometheus_name
        if not raw_name:
            continue
        bucket = buckets[raw_name]
        bucket["excl_ns"].update(extract_label_alternatives(alert.condition, NAMESPACE_LABEL_KEYS, exclude=True))
        bucket["incl_ns"].update(extract_label_alternatives(alert.condition, NAMESPACE_LABEL_KEYS, exclude=False))
        bucket["excl_jobs"].update(extract_label_alternatives(alert.condition, JOB_LABEL_KEYS, exclude=True))

    return {
        raw_name: (sorted(b["excl_ns"]), sorted(b["incl_ns"]), sorted(b["excl_jobs"]))
        for raw_name, b in buckets.items()
    }


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
        import re
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
