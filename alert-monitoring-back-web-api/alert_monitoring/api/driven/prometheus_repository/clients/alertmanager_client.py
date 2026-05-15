import logging
import os
import tempfile
from typing import List

import requests

from alert_monitoring.api.driven.prometheus_repository.models.cluster_config import ClusterConfig

logger = logging.getLogger(__name__)

_SILENCES_PATH = "/api/v2/silences"
_TIMEOUT = 10


class AlertManagerClient:
    def fetch_active_silences(self, cluster: ClusterConfig) -> List[dict]:
        if not cluster.alertmanager_url:
            return []

        url = cluster.alertmanager_url.rstrip("/") + _SILENCES_PATH
        headers = {"Authorization": f"Bearer {cluster.token}"}

        ca_cert_path = None
        try:
            verify: bool | str = cluster.verify_ssl
            if cluster.verify_ssl and cluster.ca_cert:
                fd, ca_cert_path = tempfile.mkstemp(prefix="am-ca-", suffix=".pem")
                with os.fdopen(fd, "w") as f:
                    f.write(cluster.ca_cert)
                verify = ca_cert_path

            response = requests.get(url, headers=headers, verify=verify, timeout=_TIMEOUT)
            response.raise_for_status()
            silences = response.json()
            return [s for s in silences if s.get("status", {}).get("state") == "active"]
        except Exception as exc:
            logger.error("Error al consultar silencios en AlertManager %s: %s", cluster.name, exc)
            return []
        finally:
            if ca_cert_path and os.path.exists(ca_cert_path):
                os.unlink(ca_cert_path)
