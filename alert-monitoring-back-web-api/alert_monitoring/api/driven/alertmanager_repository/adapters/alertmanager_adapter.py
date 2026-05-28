import logging
from typing import List, Optional

from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher
from alert_monitoring.api.driven.alertmanager_repository.clients.alertmanager_http_client import AlertManagerHttpClient
from alert_monitoring.api.driven.alertmanager_repository.config.alertmanager_settings import load_alertmanagers_from_env
from alert_monitoring.api.driven.alertmanager_repository.models.alertmanager_config import AlertManagerConfig

logger = logging.getLogger(__name__)


class AlertManagerAdapter:

    def __init__(self, client: Optional[AlertManagerHttpClient] = None) -> None:
        self.client = client or AlertManagerHttpClient()

    def fetch_active_blackouts(self, configs: Optional[List[AlertManagerConfig]] = None) -> List[Blackout]:
        configs = configs if configs is not None else load_alertmanagers_from_env()
        if not configs:
            return []
        blackouts: List[Blackout] = []
        for config in configs:
            logger.info("Recogiendo silencios activos de AlertManager %s", config.name)
            for raw in self.client.fetch_silences(config):
                blackout = self._to_domain(raw, source=config.name)
                if blackout is not None and blackout.state == "active":
                    blackouts.append(blackout)
        return blackouts

    def _to_domain(self, raw: dict, source: Optional[str] = None) -> Optional[Blackout]:
        try:
            status = raw.get("status") or {}
            matchers = [
                BlackoutMatcher(
                    name=m.get("name", ""),
                    value=m.get("value", ""),
                    is_regex=bool(m.get("isRegex", False)),
                    is_equal=bool(m.get("isEqual", True)),
                )
                for m in raw.get("matchers", []) or []
            ]
            return Blackout(
                id=str(raw.get("id", "")),
                matchers=matchers,
                starts_at=raw.get("startsAt"),
                ends_at=raw.get("endsAt"),
                created_by=raw.get("createdBy"),
                comment=raw.get("comment"),
                state=str(status.get("state", "active")),
                source=source,
            )
        except Exception as exc:
            logger.warning("Silencio AlertManager malformado, se omite: %s", exc)
            return None
