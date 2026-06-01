from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.alert_api_disabled import AlertApiDisabled


class AlertApiDisabledRepositoryPort(ABC):

    @abstractmethod
    def replace_all(self, disabled_alerts: List[AlertApiDisabled]) -> None:
        ...

    @abstractmethod
    def get_all(self, api: Optional[str] = None) -> List[AlertApiDisabled]:
        ...
