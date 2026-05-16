import re
from typing import Dict, Iterable, List, Optional, Tuple

ALL_ENVIRONMENTS: Tuple[str, ...] = ("dev", "itg", "pre", "pro")

CANAL_DISPLAY_NAMES: Dict[str, str] = {
    "msteams": "Teams",
    "teams": "Teams",
    "omi": "ServiceNow",
    "jira": "Jira",
    "mail": "Mail",
    "alertmanager": "AlertManager",
}

BOOL_CHANNEL_LABELS: Tuple[Tuple[str, str], ...] = (
    ("msteams", "Teams"),
    ("omi", "ServiceNow"),
    ("jira", "Jira"),
    ("mail", "Mail"),
)

_ENV_PATTERN = re.compile(r"\b(dev|itg|pre|pro)\d*\b", re.IGNORECASE)


def display_canal(canal: Optional[str]) -> Optional[str]:
    if not canal:
        return None
    return CANAL_DISPLAY_NAMES.get(canal.lower(), canal)


def resolve_channels_from_labels(labels: Dict[str, str]) -> List[str]:
    matches: List[str] = []
    for key, display in BOOL_CHANNEL_LABELS:
        if str(labels.get(key, "")).lower() == "true" and display not in matches:
            matches.append(display)
    return matches


def detect_environments(texts: Iterable[Optional[str]]) -> List[str]:
    found: List[str] = []
    for text in texts:
        if not text:
            continue
        for match in _ENV_PATTERN.findall(text):
            env = match.lower()
            if env not in found:
                found.append(env)
    return found


def environments_or_all(envs: List[str]) -> List[str]:
    return envs if envs else list(ALL_ENVIRONMENTS)
