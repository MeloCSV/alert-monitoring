import re
from collections import defaultdict
from typing import Iterable, List, Optional, Set, Tuple

from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_rule_repository_port import DefaultAlertRuleRepositoryPort
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.alert_override import AlertOverride


_NAMESPACE_LABEL_KEYS = ("namespace", "exported_namespace", "backend_target_name", "backend_name")
_JOB_LABEL_KEYS = ("job_name", "deployment", "horizontalpodautoscaler")


class RecomputeOverridesUseCase:
    def __init__(
        self,
        default_catalog_repository: DefaultAlertRuleRepositoryPort,
        alert_repository: AlertRepositoryPort,
        override_repository: AlertOverrideRepositoryPort,
    ):
        self.default_catalog_repository = default_catalog_repository
        self.alert_repository = alert_repository
        self.override_repository = override_repository

    def execute(self) -> int:
        default_rules = self.default_catalog_repository.get_all()
        adhoc_alerts = self.alert_repository.get_all(AlertFilter(alert_type="Ad-hoc"))

        # Build solution → set of microservices from Ad-hoc alerts
        solution_micros: dict[str, Set[str]] = defaultdict(set)
        for a in adhoc_alerts:
            if a.solution and a.solution != "unknown" and a.microservice:
                solution_micros[a.solution].add(a.microservice)

        solutions = sorted(solution_micros.keys())

        # Group default rules by technical name
        buckets: dict[str, list] = defaultdict(list)
        for rule in default_rules:
            buckets[rule.name].append(rule)

        overrides: List[AlertOverride] = []
        for name, bucket in buckets.items():
            for sol in solutions:
                micros = solution_micros[sol]
                is_disabled, is_partial, excluded_items = _evaluate(bucket, sol, micros)
                overrides.append(AlertOverride(
                    alert_name=name,
                    solution=sol,
                    is_disabled=is_disabled,
                    is_partial=is_partial,
                    excluded_items=excluded_items,
                ))

        self.override_repository.replace_all(overrides)
        return len(overrides)


def _evaluate(rules: Iterable, solution: str, micros: Set[str]) -> Tuple[bool, bool, List[str]]:
    ns_fully_excluded = False
    ns_re_included = False
    partially_excluded = False
    excluded_items: List[str] = []
    re_included_patterns: List[str] = []

    targets = {solution} | micros

    for rule in rules:
        ns_excl_alts = _extract_alternatives(rule.condition, _NAMESPACE_LABEL_KEYS, exclude=True)
        ns_incl_pattern = _extract_pattern(rule.condition, _NAMESPACE_LABEL_KEYS, exclude=False)
        job_excl_alts = _extract_alternatives(rule.condition, _JOB_LABEL_KEYS, exclude=True)

        for alt in ns_excl_alts:
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

        if ns_incl_pattern:
            re_included_patterns.append(ns_incl_pattern)
            for target in targets:
                if _regex_matches(target, ns_incl_pattern):
                    ns_re_included = True
                    break

        for alt in job_excl_alts:
            matched_target = False
            for target in targets:
                if _is_prefix_of(target, alt):
                    partially_excluded = True
                    matched_target = True
                    break
            if matched_target:
                _append_unique(excluded_items, _display_pattern(alt))

    excluded_items = [
        item for item in excluded_items
        if not any(_regex_matches(item, pat) for pat in re_included_patterns)
    ]

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


def _extract_pattern(expr: Optional[str], keys: Iterable[str], exclude: bool) -> Optional[str]:
    alts = _extract_alternatives(expr, keys, exclude)
    return "|".join(alts) if alts else None


def _extract_alternatives(expr: Optional[str], keys: Iterable[str], exclude: bool) -> List[str]:
    if not expr:
        return []
    operator = "!~" if exclude else "=~"
    alternatives: list[str] = []
    for key in keys:
        regex = rf'{key}\s*{re.escape(operator)}\s*"([^"]+)"'
        for match in re.findall(regex, expr):
            for part in match.split("|"):
                part = part.strip()
                if part and part not in alternatives:
                    alternatives.append(part)
    return alternatives


def _regex_matches(value: str, pattern: str) -> bool:
    try:
        return re.fullmatch(f"(?:{pattern})", value) is not None
    except re.error:
        return False


def _literal_prefix(alternative: str) -> str:
    """Return the leading literal characters of a regex alternative (stops at first metachar)."""
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
    """True when the literal prefix of `alternative` starts with `target-`."""
    if not target:
        return False
    lit = _literal_prefix(alternative)
    prefix = f"{target}-"
    return lit.startswith(prefix)
