import logging
from typing import List

from kubernetes import client

from alert_monitoring.api.driven.prometheus_repository.config.cluster_settings import write_ca_cert_to_tempfile
from alert_monitoring.api.driven.prometheus_repository.models.cluster_config import ClusterConfig
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule

logger = logging.getLogger(__name__)

GROUP = "monitoring.coreos.com"
VERSION = "v1"
PLURAL = "prometheusrules"


class KubernetesPrometheusClient:
    def fetch_rules(self, cluster: ClusterConfig) -> List[PrometheusRule]:
        api = self._build_api(cluster)
        try:
            response = api.list_namespaced_custom_object(group=GROUP, version=VERSION, plural=PLURAL, namespace=cluster.namespace)
        except client.ApiException as exc:
            logger.error("Error al consultar PrometheusRules en %s: %s", cluster.name, exc)
            return []

        rules: List[PrometheusRule] = []
        for item in response.get("items", []):
            rules.extend(self._parse_item(item))
        return rules

    def _build_api(self, cluster: ClusterConfig) -> client.CustomObjectsApi:
        configuration = client.Configuration()
        configuration.host = cluster.host
        configuration.api_key = {"authorization": f"Bearer {cluster.token}"}
        if cluster.verify_ssl and cluster.ca_cert:
            configuration.ssl_ca_cert = write_ca_cert_to_tempfile(cluster.ca_cert)
            configuration.verify_ssl = True
        else:
            configuration.verify_ssl = cluster.verify_ssl
        return client.CustomObjectsApi(client.ApiClient(configuration))

    def _parse_item(self, item: dict) -> List[PrometheusRule]:
        spec = item.get("spec", {}) or {}
        rule_file = (item.get("metadata") or {}).get("name", "")
        rules: List[PrometheusRule] = []
        for group in spec.get("groups", []) or []:
            group_name = group.get("name", "")
            for rule in group.get("rules", []) or []:
                if "alert" not in rule:
                    continue
                rules.append(PrometheusRule(
                    alert=rule.get("alert"),
                    expr=rule.get("expr", ""),
                    labels=rule.get("labels", {}) or {},
                    annotations=rule.get("annotations", {}) or {},
                    group_name=group_name,
                    rule_file=rule_file,
                ))
        return rules