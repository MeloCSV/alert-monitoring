import json
import logging
import os
from typing import List

from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig

logger = logging.getLogger(__name__)

ENV_VAR_ELASTIC_GCP = "KIBANA_ELASTIC_GCP"
ENV_VAR_ELASTIC = "KIBANA_ELASTIC"


def _load_from_env(env_var: str) -> List[KibanaConfig]:
    raw = os.environ.get(env_var)
    if not raw:
        logger.warning("Variable de entorno %s no definida; no se consultará ningún Kibana.", env_var)
        return []

    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("No se puede parsear %s como JSON: %s", env_var, exc)
        return []

    if not isinstance(items, list):
        logger.error("%s debe ser una lista JSON de Kibanas.", env_var)
        return []

    configs: List[KibanaConfig] = []
    for item in items:
        try:
            configs.append(KibanaConfig(
                name=item["name"],
                base_url=item["base_url"],
                api_key=item["api_key"],
                space_id=item.get("space_id"),
                verify_ssl=item.get("verify_ssl", True),
                per_page=item.get("per_page", 100),
                max_pages=item.get("max_pages", 100),
            ))
        except KeyError as exc:
            logger.error("Kibana mal configurado, falta el campo %s: %s", exc, item.get("name", "?"))
    return configs


def load_kibana_elastic_gcp_from_env() -> List[KibanaConfig]:
    return _load_from_env(ENV_VAR_ELASTIC_GCP)


def load_kibana_elastic_from_env() -> List[KibanaConfig]:
    return _load_from_env(ENV_VAR_ELASTIC)
