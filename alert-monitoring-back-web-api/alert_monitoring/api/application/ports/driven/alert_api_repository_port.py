from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.alert_api import AlertApi


class AlertApiRepositoryPort(ABC):

    @abstractmethod
    def save_all(self, alerts: List[AlertApi]) -> None:
        pass

    @abstractmethod
    def delete_all(self) -> None:
        pass

    @abstractmethod
    def get_all(self, apis: Optional[List[str]] = None) -> List[AlertApi]:
        pass
