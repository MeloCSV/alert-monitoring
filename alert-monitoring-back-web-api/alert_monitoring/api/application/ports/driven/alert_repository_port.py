from abc import ABC, abstractmethod
from typing import List
from alert_monitoring.api.domain.models.alert import Alert

class AlertRepositoryPort(ABC):

    @abstractmethod
    def save_all(self, alerts: List[Alert]) -> None:
        pass

    @abstractmethod
    def get_all(self) -> List[Alert]:
        pass