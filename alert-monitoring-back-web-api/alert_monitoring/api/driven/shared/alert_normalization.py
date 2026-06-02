import re
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

ALL_ENVIRONMENTS: Tuple[str, ...] = ("dev", "itg", "pre", "pro")

NAMESPACE_LABEL_KEYS: Tuple[str, ...] = ("namespace", "exported_namespace", "backend_target_name", "backend_name")
JOB_LABEL_KEYS: Tuple[str, ...] = ("job_name", "deployment", "horizontalpodautoscaler")

# Etiquetas de job que se muestran como chip en alertas Ad-hoc cuando hay granularidad de job.
ADHOC_JOB_CHIP_LABEL_KEYS: Tuple[str, ...] = (
    "job_name", "deployment", "horizontalpodautoscaler", "cronjob",
)

# Lookup de traducción: raw_name → (display_name, display_description).
# NO es la fuente de verdad de qué alertas existen; eso lo son las Prometheus rules.
# Si un raw_name nuevo aparece en Prometheus y no está aquí, se mostrará el raw_name en la UI
# hasta que alguien añada la traducción correspondiente.
DEFAULT_ALERT_DISPLAY: Dict[str, Tuple[str, str]] = {
    "Default_Service_Status_KO": (
        "Servicio sin réplicas activas",
        "El microservicio no tiene ninguna réplica levantada. El servicio está completamente caído y no puede atender peticiones.",
    ),
    "Default_Service_Status_Degraded": (
        "Servicio con réplicas insuficientes",
        "El microservicio no tiene todas sus réplicas disponibles. El servicio funciona de forma degradada con menos instancias de las configuradas.",
    ),
    "Default_Deployment_Status_Unavailable": (
        "Deployment no disponible",
        "El deployment no está disponible según Kubernetes. La condición 'Available' es false durante más de 10 minutos.",
    ),
    "Default_High_4xx_Http_Requests_Principal": (
        "Alto porcentaje de errores HTTP 4xx (>5%)",
        "Más del 5% de las peticiones HTTP están respondiendo con errores 4xx (p. ej. 404 Not Found, 401 Unauthorized). Puede indicar peticiones incorrectas o problemas de configuración.",
    ),
    "Default_High_5xx_Http_Requests_Principal": (
        "Alto porcentaje de errores HTTP 5xx (>5%)",
        "Más del 5% de las peticiones HTTP están respondiendo con errores 5xx (errores internos del servidor). El servicio está fallando al procesar las peticiones.",
    ),
    "Default_High_4xx_Http_Requests_Critical": (
        "Porcentaje crítico de errores HTTP 4xx (>10%)",
        "Más del 10% de las peticiones HTTP están respondiendo con errores 4xx. Nivel crítico de errores de cliente que requiere atención inmediata.",
    ),
    "Default_High_5xx_Http_Requests_Critical": (
        "Porcentaje crítico de errores HTTP 5xx (>10%)",
        "Más del 10% de las peticiones HTTP están respondiendo con errores 5xx (errores internos del servidor). Nivel crítico de fallos que requiere atención inmediata.",
    ),
    "Default_JobFailed": (
        "Job de Kubernetes finalizado con error",
        "Un job de Kubernetes ha terminado en estado fallido. Puede tratarse de un CronJob que no se ejecutó correctamente.",
    ),
    "Default_JobSuspended": (
        "Job de Kubernetes suspendido",
        "Un job de Kubernetes está en estado suspendido. No ejecutará ninguna tarea hasta que sea reanudado manualmente.",
    ),
    "Default_JobExecutionMissed": (
        "Job no ejecutado según su planificación",
        "Un job programado lleva más de 5 minutos en estado Pending o Unknown. El pod no se ha ejecutado en el tiempo esperado.",
    ),
    "Default_CPURequestQuotaReached": (
        "Cuota de CPU request al 90%",
        "El namespace ha consumido el 90% de su cuota de CPU (requests). Si se alcanza el 100%, Kubernetes no podrá programar nuevos pods en este namespace.",
    ),
    "Default_MemoryLimitQuotaReached": (
        "Cuota de memoria limit al 90%",
        "El namespace ha consumido el 90% de su cuota de memoria (limits). Superar el límite puede provocar que Kubernetes elimine pods por exceso de memoria.",
    ),
    "Default_MemoryRequestQuotaReached": (
        "Cuota de memoria request al 90%",
        "El namespace ha consumido el 90% de su cuota de memoria (requests). Si se alcanza el 100%, Kubernetes no podrá programar nuevos pods en este namespace.",
    ),
    "Default_CpuUsageHigh": (
        "Uso de CPU superior al 90% del límite",
        "El namespace está usando más del 90% de su límite de CPU. Esto puede causar throttling (ralentización) en los servicios y degradar el rendimiento.",
    ),
    "Default_HPAMaximumReplicasForTooLong": (
        "HPA en máximo de réplicas durante más de 1 hora",
        "El autoescalador horizontal (HPA) lleva más de 1 hora con el número máximo de réplicas activas. No puede escalar más y el sistema podría estar bajo una presión sostenida.",
    ),
    # Kibana global alerts
    "Errores Totales 15% GCP (old)": (
        "Errores Totales 15% GCP (old)",
        "Errores 5XX totales en GCP ha llegado al 15% en los últimos 10 segundos.",
    ),
    "Errores Totales 15% OCP [old]": (
        "Errores Totales 15% OCP [old]",
        "Errores 5XX totales en OCP ha llegado al 15% en los últimos 10 segundos.",
    ),
    "Errores Totales 15% OCP SOAP [old]": (
        "Errores Totales 15% OCP SOAP [old]",
        "Errores 5XX totales en OCP (SOAP) ha llegado al 15% en los últimos 10 segundos.",
    ),
    "SLAs - Test": (
        "SLAs - Test",
        "La duración de las peticiones está superando el SLA definido.",
    ),
    "SLAs - Deterioro del servicio": (
        "SLAs - Deterioro del servicio",
        "La latencia de las peticiones ha superado el SLA definido del servicio.",
    ),
    "Errores Totales 15% GCP": (
        "Errores Totales 15% GCP",
        "Errores 5XX totales en GCP ha llegado al 15% en los últimos 2 minutos.",
    ),
    "Errores Totales 15% OCP SOAP": (
        "Errores Totales 15% OCP SOAP",
        "Errores 5XX totales en OCP (SOAP) ha llegado al 15% en los últimos 2 minutos.",
    ),
    "Errores 500 por API y método": (
        "Errores 500 por API y método",
        "El ratio de errores 5XX ha superado el umbral para una API y método concretos.",
    ),
    "Errores 500 por pod [OCP] [SOAP]": (
        "Errores 500 por pod [OCP] [SOAP]",
        "El ratio de errores en un pod de OCP (SOAP) ha alcanzado el 100%.",
    ),
    "Errores 500 por pod [OCP]": (
        "Errores 500 por pod [OCP]",
        "El ratio de errores en un pod de OCP ha alcanzado el 100%.",
    ),
    "Errores Totales 15% OCP": (
        "Errores Totales 15% OCP",
        "Errores 5XX totales en OCP ha llegado al 15% en los últimos 2 minutos.",
    ),
    "SLAs - Afectación del servicio": (
        "SLAs - Afectación del servicio",
        "La duración de las peticiones está superando el SLA definido del método.",
    ),
    "Errores 400 por API y método": (
        "Errores 400 por API y método",
        "El ratio de errores 4XX ha superado el umbral para una API y método concretos.",
    ),
    "Errores 500 por pod [GCP]": (
        "Errores 500 por pod [GCP]",
        "El ratio de errores en un pod de GCP ha alcanzado el 100%.",
    ),
}

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


def extract_label_alternatives(expr: Optional[str], keys: Iterable[str], exclude: bool) -> List[str]:
    """Extract the alternatives from a PromQL selector for the given label keys.

    Args:
        expr: PromQL expression string.
        keys: Label names to look for (e.g. ``namespace``, ``job_name``).
        exclude: If True look for ``!~`` selectors; if False look for ``=~``.
    """
    if not expr:
        return []
    operator = "!~" if exclude else "=~"
    alternatives: List[str] = []
    for key in keys:
        regex = rf'{key}\s*{re.escape(operator)}\s*"([^"]+)"'
        for match in re.findall(regex, expr):
            for part in _split_top_level_alternatives(match):
                if part and part not in alternatives:
                    alternatives.append(part)
    return alternatives


def build_exclusion_updates(default_rules) -> dict:
    """Merge exclusion patterns from all default Prometheus rule instances grouped by raw_name."""
    buckets: dict[str, dict] = defaultdict(lambda: {"excl_ns": set(), "incl_ns": set(), "excl_jobs": set()})
    for rule in default_rules:
        raw_name = rule.alert.split()[0] if rule.alert else None
        if not raw_name:
            continue
        bucket = buckets[raw_name]
        bucket["excl_ns"].update(extract_label_alternatives(rule.expr, NAMESPACE_LABEL_KEYS, exclude=True))
        bucket["incl_ns"].update(extract_label_alternatives(rule.expr, NAMESPACE_LABEL_KEYS, exclude=False))
        bucket["excl_jobs"].update(extract_label_alternatives(rule.expr, JOB_LABEL_KEYS, exclude=True))
    return {
        raw_name: (sorted(b["excl_ns"]), sorted(b["incl_ns"]), sorted(b["excl_jobs"]))
        for raw_name, b in buckets.items()
    }


def clean_label_value(value: str) -> str:
    """Limpia el valor de una etiqueta para mostrarlo: quita anclas/comodines de regex."""
    cleaned = value.strip()
    if cleaned.startswith("^"):
        cleaned = cleaned[1:]
    if cleaned.endswith("$"):
        cleaned = cleaned[:-1]
    for suffix in (".*", ".+"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return cleaned.rstrip("-").strip()


def extract_adhoc_chips(expr: Optional[str]) -> List[str]:
    """Extrae chips para alertas Ad-hoc.

    Si hay selectores de job (job_name, deployment, etc.) se devuelven esos.
    Si solo hay selectores de namespace (namespace entero incluido), se devuelve
    lista vacía porque no hay granularidad adicional que mostrar.
    """
    if not expr:
        return []
    job_chips: List[str] = []
    for key in ADHOC_JOB_CHIP_LABEL_KEYS:
        regex = rf'{key}\s*=~?\s*"([^"]+)"'
        for match in re.findall(regex, expr):
            for raw in match.split("|"):
                cleaned = clean_label_value(raw)
                if cleaned and cleaned not in job_chips:
                    job_chips.append(cleaned)
    return job_chips


def _split_top_level_alternatives(pattern: str) -> List[str]:
    """Split a regex alternation string on top-level '|' only (not inside parentheses)."""
    parts: List[str] = []
    depth = 0
    current: List[str] = []
    for ch in pattern:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "|" and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(ch)
    if current:
        part = "".join(current).strip()
        if part:
            parts.append(part)
    return parts
