from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.alert_override import AlertOverride


class AlertOverrideRepositoryPort(ABC):

    @abstractmethod
    def replace_all(self, overrides: List[AlertOverride]) -> None:
        pass

    @abstractmethod
    def get_all(self, solution: Optional[str] = None) -> List[AlertOverride]:
        pass
