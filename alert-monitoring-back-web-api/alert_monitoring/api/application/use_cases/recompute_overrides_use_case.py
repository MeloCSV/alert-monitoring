import re
from collections import defaultdict
from typing import Iterable, List, Optional, Tuple

from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_override import AlertOverride


_NAMESPACE_LABEL_KEYS = ("namespace", "backend_target_name", "backend_name")
_JOB_LABEL_KEYS = ("job_name", "deployment")


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
                is_disabled, is_partial = self._evaluate(bucket, micro)
                overrides.append(AlertOverride(
                    alert_name=name,
                    microservice=micro,
                    is_disabled=is_disabled,
                    is_partial=is_partial,
                ))

        self.override_repository.replace_all(overrides)
        return len(overrides)

    @classmethod
    def _evaluate(cls, rules: Iterable[Alert], microservice: str) -> Tuple[bool, bool]:
        ns_excluded_anywhere = False
        ns_re_included_anywhere = False
        job_excluded_anywhere = False

        for rule in rules:
            ns_excl = _extract_pattern(rule.condition, _NAMESPACE_LABEL_KEYS, exclude=True)
            ns_incl = _extract_pattern(rule.condition, _NAMESPACE_LABEL_KEYS, exclude=False)
            job_excl_alts = _extract_alternatives(rule.condition, _JOB_LABEL_KEYS, exclude=True)

            if ns_excl and _regex_matches(microservice, ns_excl):
                ns_excluded_anywhere = True
            if ns_incl and _regex_matches(microservice, ns_incl):
                ns_re_included_anywhere = True
            if job_excl_alts and _job_excludes_microservice(job_excl_alts, microservice):
                job_excluded_anywhere = True

        is_disabled = ns_excluded_anywhere and not ns_re_included_anywhere
        is_partial = job_excluded_anywhere and not is_disabled
        return is_disabled, is_partial


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


def _job_excludes_microservice(alternatives: List[str], microservice: str) -> bool:
    if not microservice:
        return False
    prefix = f"{microservice}-"
    for alt in alternatives:
        literal = _literal_prefix(alt)
        if not literal:
            continue
        if literal == microservice or literal.startswith(prefix):
            return True
    return False


def _literal_prefix(alternative: str) -> str:
    literal_chars: list[str] = []
    i = 0
    while i < len(alternative):
        ch = alternative[i]
        if ch == "\\" and i + 1 < len(alternative):
            literal_chars.append(alternative[i + 1])
            i += 2
            continue
        if ch in ".*+?()[]{}|^$":
            break
        literal_chars.append(ch)
        i += 1
    return "".join(literal_chars)
