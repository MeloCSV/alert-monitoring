import logging
from typing import List, Optional, Tuple

from alert_monitoring.api.driven.kibana_repository.clients.kibana_http_client import KibanaHttpClient
from alert_monitoring.api.driven.kibana_repository.config.kibana_settings import (
    load_kibana_elastic_from_env,
    load_kibana_elastic_gcp_from_env,
)
from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig

logger = logging.getLogger(__name__)


class KibanaAdapter:

    def __init__(self, client: Optional[KibanaHttpClient] = None) -> None:
        self.client = client or KibanaHttpClient()

    def fetch_rules(self, configs: Optional[List[KibanaConfig]] = None) -> List[dict]:
        configs = configs if configs is not None else load_kibana_elastic_gcp_from_env()
        if not configs:
            return []

        rules: List[dict] = []
        for config in configs:
            logger.info("Recogiendo reglas de alerting de Kibana %s", config.name)
            rules.extend(self.client.fetch_rules(config))
        return rules

    def fetch_rules_by_config(
        self, configs: Optional[List[KibanaConfig]] = None
    ) -> List[Tuple[KibanaConfig, List[dict]]]:
        configs = configs if configs is not None else load_kibana_elastic_from_env()
        if not configs:
            return []

        result: List[Tuple[KibanaConfig, List[dict]]] = []
        for config in configs:
            logger.info("Recogiendo reglas de alerting de Kibana %s", config.name)
            result.append((config, self.client.fetch_rules(config)))
        return result
