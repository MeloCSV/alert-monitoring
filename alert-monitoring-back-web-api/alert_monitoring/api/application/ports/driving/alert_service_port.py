from abc import ABC, abstractmethod
from typing import List, Optional
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter

class AlertServicePort(ABC):

    @abstractmethod
    def sync_prometheus_alerts(self) -> int:
        pass

    @abstractmethod
    def save_elastic_alerts(self, json_content: str) -> None:
        pass

    @abstractmethod
    def get_all_alerts(self, filters: Optional[AlertFilter] = None) -> List[Alert]:
        pass