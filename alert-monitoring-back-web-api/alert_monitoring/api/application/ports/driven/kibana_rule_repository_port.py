from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.kibana_rule import KibanaRule


class KibanaRuleRepositoryPort(ABC):

    @abstractmethod
    def save_all(self, rules: List[KibanaRule]) -> None:
        ...

    @abstractmethod
    def delete_all(self) -> None:
        ...

    @abstractmethod
    def get_all(self, api: Optional[str] = None, is_global: Optional[bool] = None) -> List[KibanaRule]:
        ...

    @abstractmethod
    def get_distinct_apis(self) -> List[str]:
        ...
