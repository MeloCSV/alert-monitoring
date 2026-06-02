from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.catalog_app import CatalogApp


class CatalogServicePort(ABC):

    @abstractmethod
    def sync_catalog(self) -> int:
        pass

    @abstractmethod
    def get_all_catalog_apps(self, name: Optional[str] = None) -> List[CatalogApp]:
        pass
