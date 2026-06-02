from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.catalog_app import CatalogApp


class CatalogAppRepositoryPort(ABC):

    @abstractmethod
    def save_all(self, apps: List[CatalogApp]) -> None:
        pass

    @abstractmethod
    def get_all(self, name: Optional[str] = None) -> List[CatalogApp]:
        pass
