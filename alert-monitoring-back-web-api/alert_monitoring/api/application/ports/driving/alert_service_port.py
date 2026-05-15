from abc import ABC, abstractmethod
from typing import List, Optional
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.alert_override import AlertOverride
from alert_monitoring.api.domain.models.blackout import Blackout

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

    @abstractmethod
    def get_alert_overrides(self, solution: Optional[str] = None) -> List[AlertOverride]:
        pass

    @abstractmethod
    def get_active_blackouts(self) -> List[Blackout]:
        pass