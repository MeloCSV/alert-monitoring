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
        rules: List[PrometheusRule] = []
        _continue = None

        while True:
            try:
                kwargs = {"_continue": _continue} if _continue else {}
                response = api.list_cluster_custom_object(group=GROUP, version=VERSION, plural=PLURAL, **kwargs)
            except client.ApiException as exc:
                logger.error("Error al consultar PrometheusRules en %s: %s", cluster.name, exc)
                return rules

            for item in response.get("items", []):
                rules.extend(self._parse_item(item, cluster.name))

            _continue = (response.get("metadata") or {}).get("continue")
            if not _continue:
                break

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

    def _parse_item(self, item: dict, cluster_name: str) -> List[PrometheusRule]:
        spec = item.get("spec", {}) or {}
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
                    cluster=cluster_name,
                ))
        return rules