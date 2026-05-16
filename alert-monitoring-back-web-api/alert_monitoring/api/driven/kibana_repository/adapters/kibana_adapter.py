import logging
from typing import List, Optional

from alert_monitoring.api.driven.kibana_repository.clients.kibana_http_client import KibanaHttpClient
from alert_monitoring.api.driven.kibana_repository.config.kibana_settings import load_kibanas_from_env
from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig

logger = logging.getLogger(__name__)


class KibanaAdapter:

    def __init__(self, client: Optional[KibanaHttpClient] = None) -> None:
        self.client = client or KibanaHttpClient()

    def fetch_rules(self, configs: Optional[List[KibanaConfig]] = None) -> List[dict]:
        configs = configs if configs is not None else load_kibanas_from_env()
        if not configs:
            return []

        rules: List[dict] = []
        for config in configs:
            logger.info("Recogiendo reglas de alerting de Kibana %s", config.name)
            rules.extend(self.client.fetch_rules(config))
        return rules
