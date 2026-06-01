from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi


class CatalogAppApiServicePort(ABC):

    @abstractmethod
    def sync_catalog_app_api(self) -> int:
        pass

    @abstractmethod
    def get_all(self, app: Optional[str] = None) -> List[CatalogAppApi]:
        pass
