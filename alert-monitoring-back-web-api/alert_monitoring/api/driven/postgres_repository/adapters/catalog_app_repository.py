from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_model import CatalogAppDB
from alert_monitoring.api.driven.postgres_repository.mappers.catalog_app_db_mapper import CatalogAppDBMapper
from alert_monitoring.api.driven.postgres_repository.sync_helpers import reconcile_by_key


class CatalogAppRepositoryAdapter(CatalogAppRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, catalog_app_db_mapper: CatalogAppDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.catalog_app_db_mapper = catalog_app_db_mapper
        self.logger = logger

    def save_all(self, apps: List[CatalogApp]) -> None:
        self.logger.info(f"Sincronizando {len(apps)} aplicaciones del catálogo")
        reconcile_by_key(
            self.sqlalchemy_repository,
            CatalogAppDB,
            apps,
            key_attr="object_id",
            apply_fn=self._apply,
        )

    @staticmethod
    def _apply(row: CatalogAppDB, app: CatalogApp) -> None:
        row.object_id = app.object_id
        row.name = app.name
        row.csw_code = app.csw_code

    def get_all(self, name: Optional[str] = None) -> List[CatalogApp]:
        self.logger.info(f"Consultando catálogo name={name}")
        query = self.sqlalchemy_repository.query(CatalogAppDB)

        if name:
            query = query.filter(CatalogAppDB.name.ilike(f"%{name}%"))

        return self.catalog_app_db_mapper.to_domain_list(query.order_by(CatalogAppDB.name).all())
