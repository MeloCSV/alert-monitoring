import logging
from typing import List

import httpx

from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig

logger = logging.getLogger(__name__)

RULES_FIND_PATH = "/api/alerting/rules/_find"
DEFAULT_TIMEOUT = 30.0


class KibanaHttpClient:

    def fetch_rules(self, config: KibanaConfig) -> List[dict]:
        url = self._build_url(config)
        headers = {
            "Authorization": f"ApiKey {config.api_key}",
            "kbn-xsrf": "true",
            "Accept": "application/json",
        }

        rules: List[dict] = []
        with httpx.Client(verify=config.verify_ssl, timeout=DEFAULT_TIMEOUT) as client:
            for page in range(1, config.max_pages + 1):
                params = {"page": page, "per_page": config.per_page}
                try:
                    response = client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    logger.error("Error al consultar reglas en Kibana %s (page=%s): %s", config.name, page, exc)
                    return rules

                payload = response.json()
                data = payload.get("data") if isinstance(payload, dict) else None
                if not isinstance(data, list):
                    logger.error("Respuesta inesperada de Kibana %s: se esperaba 'data' como lista", config.name)
                    return rules

                rules.extend(data)

                total = payload.get("total", 0)
                if len(rules) >= total or not data:
                    break
            else:
                logger.warning(
                    "Se alcanzó max_pages=%s en Kibana %s; puede haber reglas sin sincronizar.",
                    config.max_pages, config.name,
                )

        return rules

    def _build_url(self, config: KibanaConfig) -> str:
        base = config.base_url.rstrip("/")
        if config.space_id:
            return f"{base}/s/{config.space_id}{RULES_FIND_PATH}"
        return f"{base}{RULES_FIND_PATH}"
