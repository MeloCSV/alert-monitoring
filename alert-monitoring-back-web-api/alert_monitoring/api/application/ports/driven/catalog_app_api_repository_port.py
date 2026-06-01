from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi


class CatalogAppApiRepositoryPort(ABC):

    @abstractmethod
    def replace_all(self, items: List[CatalogAppApi]) -> None:
        pass

    @abstractmethod
    def get_all(self, app: Optional[str] = None) -> List[CatalogAppApi]:
        pass
