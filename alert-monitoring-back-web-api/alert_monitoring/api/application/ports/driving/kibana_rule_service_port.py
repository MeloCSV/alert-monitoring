from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.kibana_rule import KibanaRule


class KibanaRuleServicePort(ABC):

    @abstractmethod
    def sync_kibana_rules(self) -> int:
        ...

    @abstractmethod
    def get_rules(self, api: Optional[str] = None, is_global: Optional[bool] = None) -> List[KibanaRule]:
        ...

    @abstractmethod
    def get_apis(self) -> List[str]:
        ...
