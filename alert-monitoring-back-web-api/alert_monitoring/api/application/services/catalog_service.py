from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.catalog_service_port import CatalogServicePort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.driven.atlassian_assets_repository.adapters.atlassian_assets_adapter import AtlassianAssetsAdapter


class CatalogService(CatalogServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(self, catalog_app_repository: CatalogAppRepositoryPort, logger: LoggerSetup):
        self.catalog_app_repository = catalog_app_repository
        self.atlassian_assets_adapter = AtlassianAssetsAdapter()
        self.logger = logger

    def sync_catalog(self) -> int:
        self.logger.info("sync_catalog")
        apps = self.atlassian_assets_adapter.fetch_catalog_apps()
        self.catalog_app_repository.save_all(apps)
        return len(apps)

    def get_all_catalog_apps(self, name: Optional[str] = None) -> List[CatalogApp]:
        self.logger.info(f"get_all_catalog_apps name={name}")
        return self.catalog_app_repository.get_all(name=name)
