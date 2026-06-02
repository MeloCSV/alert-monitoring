from abc import ABC, abstractmethod
from typing import List, Optional
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.blackout import Blackout
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.solution_view import SolutionView
from alert_monitoring.api.domain.models.api_solution_view import ApiSolutionView


class AlertServicePort(ABC):

    @abstractmethod
    def sync_prometheus_alerts(self) -> int:
        pass

    @abstractmethod
    def sync_elastic_alerts(self) -> int:
        pass

    @abstractmethod
    def get_all_alerts(self, filters: Optional[AlertFilter] = None) -> List[Alert]:
        pass

    @abstractmethod
    def get_active_blackouts(self, solution: Optional[str] = None) -> List[Blackout]:
        pass

    @abstractmethod
    def get_default_alerts(self) -> List[DefaultAlert]:
        pass

    @abstractmethod
    def get_solution_view(self, solution: str) -> SolutionView:
        pass

    @abstractmethod
    def get_api_solution_view(self, app: str) -> ApiSolutionView:
        pass
