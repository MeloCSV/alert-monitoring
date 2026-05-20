from abc import ABC, abstractmethod
from typing import List

from alert_monitoring.api.domain.models.default_alert import DefaultAlert


class DefaultAlertRepositoryPort(ABC):

    @abstractmethod
    def get_all(self) -> List[DefaultAlert]:
        pass

    @abstractmethod
    def upsert_batch(self, alerts: List[DefaultAlert]) -> None:
        """Upsert a batch of default alerts from Prometheus sync.

        For each alert:
        - If raw_name is new: INSERT all fields.
        - If raw_name exists: UPDATE raw_description, excluded_*, included_*,
          severity and notification_channel. Only update display_name and
          display_description when they are currently NULL (preserves manual edits).
        """
        pass
