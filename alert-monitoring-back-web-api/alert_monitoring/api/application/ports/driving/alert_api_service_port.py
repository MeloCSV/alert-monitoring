from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.alert_api import AlertApi


class AlertApiServicePort(ABC):

    @abstractmethod
    def sync_alert_apis(self) -> int:
        ...

    @abstractmethod
    def get_alert_apis(self, api: Optional[str] = None) -> List[AlertApi]:
        ...

    @abstractmethod
    def get_apis(self) -> List[str]:
        ...
