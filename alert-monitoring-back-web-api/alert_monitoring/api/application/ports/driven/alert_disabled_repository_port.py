from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.alert_disabled import AlertDisabled


class AlertDisabledRepositoryPort(ABC):

    @abstractmethod
    def replace_all(self, disabled_alerts: List[AlertDisabled]) -> None:
        pass

    @abstractmethod
    def get_all(self, solution: Optional[str] = None) -> List[AlertDisabled]:
        pass
