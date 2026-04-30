from abc import ABC, abstractmethod
from typing import List
from alert_monitoring.api.domain.models.alert import Alert

class AlertServicePort(ABC):

    @abstractmethod
    def save_alerts(self, yaml_content: str) -> None:
        pass

    @abstractmethod
    def save_elastic_alerts(self, json_content: str) -> None:
        pass

    @abstractmethod
    def get_all_alerts(self) -> List[Alert]:
        pass