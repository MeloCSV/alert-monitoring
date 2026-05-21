from abc import ABC, abstractmethod
from typing import List, Optional
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter

class AlertRepositoryPort(ABC):

    @abstractmethod
    def save_all(self, alerts: List[Alert]) -> None:
        pass

    @abstractmethod
    def delete_by_source_tool(self, source_tool: str) -> None:
        pass

    @abstractmethod
    def get_all(self, filters:Optional[AlertFilter] = None) -> List[Alert]:
        pass