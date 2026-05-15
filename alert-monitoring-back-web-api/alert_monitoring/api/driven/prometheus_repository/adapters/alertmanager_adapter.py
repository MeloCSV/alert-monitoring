import logging
from typing import List

from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher
from alert_monitoring.api.driven.prometheus_repository.clients.alertmanager_client import AlertManagerClient
from alert_monitoring.api.driven.prometheus_repository.config.cluster_settings import load_clusters_from_env
from alert_monitoring.api.driven.prometheus_repository.models.cluster_config import ClusterConfig

logger = logging.getLogger(__name__)


class AlertManagerAdapter:
    def __init__(self, client: AlertManagerClient | None = None) -> None:
        self.client = client or AlertManagerClient()

    def fetch_active_blackouts(self, clusters: List[ClusterConfig] | None = None) -> List[Blackout]:
        clusters = clusters if clusters is not None else load_clusters_from_env()
        blackouts: List[Blackout] = []
        for cluster in clusters:
            silences = self.client.fetch_active_silences(cluster)
            blackouts.extend(self._to_blackout(s, cluster.name) for s in silences)
        return blackouts

    def _to_blackout(self, silence: dict, cluster_name: str) -> Blackout:
        return Blackout(
            id=silence.get("id", ""),
            cluster=cluster_name,
            matchers=[
                BlackoutMatcher(
                    name=m.get("name", ""),
                    value=m.get("value", ""),
                    isRegex=m.get("isRegex", False),
                    isEqual=m.get("isEqual", True),
                )
                for m in silence.get("matchers", [])
            ],
            starts_at=silence.get("startsAt", ""),
            ends_at=silence.get("endsAt", ""),
            created_by=silence.get("createdBy", ""),
            comment=silence.get("comment", ""),
        )
