from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from alert_monitoring.api.domain.models.default_alert import DefaultAlert


class DefaultAlertRepositoryPort(ABC):

    @abstractmethod
    def get_all(self) -> List[DefaultAlert]:
        pass

    @abstractmethod
    def replace_exclusions(self, updates: Dict[str, Tuple[List[str], List[str], List[str]]]) -> None:
        """Replace exclusion patterns for all default alerts in one transaction.

        Args:
            updates: mapping raw_name → (excluded_namespaces, included_namespaces, excluded_jobs)
        """
        pass

    @abstractmethod
    def update_raw_description(self, raw_name: str, raw_description: str) -> None:
        pass
