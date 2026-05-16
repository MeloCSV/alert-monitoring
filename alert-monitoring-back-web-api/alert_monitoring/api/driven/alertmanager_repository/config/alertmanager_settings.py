import json
import logging
import os
from typing import List

from alert_monitoring.api.driven.alertmanager_repository.models.alertmanager_config import AlertManagerConfig

logger = logging.getLogger(__name__)

ENV_VAR = "ALERTMANAGERS"


def load_alertmanagers_from_env() -> List[AlertManagerConfig]:
    raw = os.environ.get(ENV_VAR)
    if not raw:
        logger.warning("Variable de entorno %s no definida; no se consultará ningún AlertManager.", ENV_VAR)
        return []

    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("No se puede parsear %s como JSON: %s", ENV_VAR, exc)
        return []

    if not isinstance(items, list):
        logger.error("%s debe ser una lista JSON de AlertManagers.", ENV_VAR)
        return []

    configs: List[AlertManagerConfig] = []
    for item in items:
        try:
            configs.append(AlertManagerConfig(
                name=item["name"],
                url=item["url"],
                token=item.get("token"),
                verify_ssl=item.get("verify_ssl", True),
                host_header=item.get("host_header"),
                sni_hostname=item.get("sni_hostname"),
            ))
        except KeyError as exc:
            logger.error("AlertManager mal configurado, falta el campo %s: %s", exc, item.get("name", "?"))
    return configs
