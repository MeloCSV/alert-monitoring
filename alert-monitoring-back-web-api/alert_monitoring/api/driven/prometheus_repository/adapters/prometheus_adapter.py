import logging
from typing import List
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule

from alert_monitoring.api.driven.prometheus_repository.clients.kubernetes_prometheus_client import ( KubernetesPrometheusClient)
from alert_monitoring.api.driven.prometheus_repository.config.cluster_settings import load_clusters_from_env
from alert_monitoring.api.driven.prometheus_repository.models.cluster_config import ClusterConfig

logger = logging.getLogger(__name__)

class PrometheusAdapter:
        
    def __init__(self, client: KubernetesPrometheusClient | None = None) -> None:
        self.client = client or KubernetesPrometheusClient()
    
    def fetch_rules(self, clusters: List[ClusterConfig] | None = None) -> List[PrometheusRule]:
        clusters = clusters if clusters is not None else load_clusters_from_env()
        if not clusters:
            return []
        rules: List[PrometheusRule] = []
        for cluster in clusters:
            logger.info("Recogiendo PrometheusRules del cluster %s", cluster.name)
            cluster_rules = self.client.fetch_rules(cluster)
            for rule in cluster_rules:
                rule.cluster_name = cluster.name
            rules.extend(cluster_rules)
        return rules