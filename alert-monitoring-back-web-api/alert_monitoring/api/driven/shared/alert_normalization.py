import re
from typing import Dict, Iterable, List, Optional, Tuple

ALL_ENVIRONMENTS: Tuple[str, ...] = ("dev", "itg", "pre", "pro")

NAMESPACE_LABEL_KEYS: Tuple[str, ...] = ("namespace", "exported_namespace", "backend_target_name", "backend_name")
JOB_LABEL_KEYS: Tuple[str, ...] = ("job_name", "deployment", "horizontalpodautoscaler")

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
    "Default_PodCrashLoopingPrincipal": (
        "Pod reiniciándose continuamente (principal)",
        "Un pod del entorno principal del microservicio está en CrashLoopBackOff. Kubernetes lo está reiniciando repetidamente debido a fallos continuos.",
    ),
    "Default_PodCrashLoopingCritical": (
        "Pod reiniciándose continuamente (crítico)",
        "Un pod del entorno crítico del microservicio está en CrashLoopBackOff. Kubernetes lo está reiniciando repetidamente debido a fallos continuos.",
    ),
    "High_4xx_Http_Requests_Principal": (
        "Alto porcentaje de errores HTTP 4xx (>5%)",
        "Más del 5% de las peticiones HTTP están respondiendo con errores 4xx (p. ej. 404 Not Found, 401 Unauthorized). Puede indicar peticiones incorrectas o problemas de configuración.",
    ),
    "High_4xx_Http_Requests_Critical": (
        "Porcentaje crítico de errores HTTP 4xx (>10%)",
        "Más del 10% de las peticiones HTTP están respondiendo con errores 4xx. Nivel crítico de errores de cliente que requiere atención inmediata.",
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
            for part in match.split("|"):
                part = part.strip()
                if part and part not in alternatives:
                    alternatives.append(part)
    return alternatives
