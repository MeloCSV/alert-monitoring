from abc import ABC, abstractmethod
from typing import List
from alert_monitoring.api.domain.models.default_alert_rule import DefaultAlertRule

class DefaultAlertRuleRepositoryPort(ABC):
    @abstractmethod
    def replace_for_cluster(self, cluster: str, rules: List[DefaultAlertRule]) -> None:
        pass

    @abstractmethod
    def get_all(self) -> List[DefaultAlertRule]:
        pass
