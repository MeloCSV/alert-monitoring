import logging
from typing import List

import httpx

from alert_monitoring.api.driven.alertmanager_repository.models.alertmanager_config import AlertManagerConfig

logger = logging.getLogger(__name__)

SILENCES_PATH = "/api/v2/silences"
DEFAULT_TIMEOUT = 10.0


class AlertManagerHttpClient:
    def fetch_silences(self, config: AlertManagerConfig) -> List[dict]:
        url = config.url.rstrip("/") + SILENCES_PATH
        headers = {}
        if config.host_header:
            headers["Host"] = config.host_header
        if config.token:
            headers["Authorization"] = f"Bearer {config.token}"
        extensions = {"sni_hostname": config.sni_hostname} if config.sni_hostname else None
        try:
            request = httpx.Request("GET", url, headers=headers, extensions=extensions)
            with httpx.Client(verify=config.verify_ssl, timeout=DEFAULT_TIMEOUT) as client:
                response = client.send(request)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Error al consultar silencios en AlertManager %s: %s", config.name, exc)
            return []

        payload = response.json()
        if not isinstance(payload, list):
            logger.error("Respuesta inesperada de %s: se esperaba lista de silencios", config.name)
            return []
        return payload
