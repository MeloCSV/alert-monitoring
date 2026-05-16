import json
import logging
import os
import tempfile
from typing import List

from alert_monitoring.api.driven.prometheus_repository.models.cluster_config import ClusterConfig

logger = logging.getLogger(__name__)

ENV_VAR = "K8S_CLUSTERS"


def load_clusters_from_env() -> List[ClusterConfig]:
    raw = os.environ.get(ENV_VAR)
    if not raw:
        logger.warning("Variable de entorno %s no definida; no se sincronizará ningún cluster.", ENV_VAR)
        return []

    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("No se puede parsear %s como JSON: %s", ENV_VAR, exc)
        return []

    if not isinstance(items, list):
        logger.error("%s debe ser una lista JSON de clusters.", ENV_VAR)
        return []

    clusters: List[ClusterConfig] = []
    for item in items:
        try:
            clusters.append(ClusterConfig(
                name=item["name"],
                host=item["host"],
                token=item["token"],
                namespace=item.get("namespace", "prometheus"),
                ca_cert=item.get("ca_cert"),
                verify_ssl=item.get("verify_ssl", True),
            ))
        except KeyError as exc:
            logger.error("Cluster mal configurado, falta el campo %s: %s", exc, item.get("name", "?"))
    return clusters


def write_ca_cert_to_tempfile(ca_cert: str) -> str:
    fd, path = tempfile.mkstemp(prefix="k8s-ca-", suffix=".pem")
    with os.fdopen(fd, "w") as f:
        f.write(ca_cert)
    return path