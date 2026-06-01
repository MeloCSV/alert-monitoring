from abc import ABC, abstractmethod
from typing import List

from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi


class DefaultAlertApiRepositoryPort(ABC):

    @abstractmethod
    def get_all(self) -> List[DefaultAlertApi]:
        ...

    @abstractmethod
    def upsert_batch(self, alerts: List[DefaultAlertApi]) -> None:
        ...

    @abstractmethod
    def delete_where_not_in(self, raw_names: List[str]) -> None:
        ...
