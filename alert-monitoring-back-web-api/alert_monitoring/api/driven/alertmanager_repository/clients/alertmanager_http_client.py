import logging
import time
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
        t0 = time.perf_counter()
        try:
            request = httpx.Request("GET", url, headers=headers, extensions=extensions)
            with httpx.Client(verify=config.verify_ssl, timeout=DEFAULT_TIMEOUT) as client:
                response = client.send(request)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.error("[TIMER] AlertManager %s → %.1f ms ERROR: %s", config.name, elapsed_ms, exc)
            return []

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("[TIMER] AlertManager %s → %.1f ms", config.name, elapsed_ms)

        payload = response.json()
        if not isinstance(payload, list):
            logger.error("Respuesta inesperada de %s: se esperaba lista de silencios", config.name)
            return []
        return payload
