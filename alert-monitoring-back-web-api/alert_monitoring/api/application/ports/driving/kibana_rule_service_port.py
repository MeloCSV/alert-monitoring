from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.kibana_rule import AlertApi


class AlertApiServicePort(ABC):

    @abstractmethod
    def sync_kibana_rules(self) -> int:
        ...

    @abstractmethod
    def get_rules(self, api: Optional[str] = None) -> List[AlertApi]:
        ...

    @abstractmethod
    def get_apis(self) -> List[str]:
        ...
