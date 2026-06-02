from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.alert_api import AlertApi


class AlertApiRepositoryPort(ABC):

    @abstractmethod
    def save_all(self, rules: List[AlertApi]) -> None:
        ...

    @abstractmethod
    def delete_all(self) -> None:
        ...

    @abstractmethod
    def get_all(self, api: Optional[str] = None) -> List[AlertApi]:
        ...
