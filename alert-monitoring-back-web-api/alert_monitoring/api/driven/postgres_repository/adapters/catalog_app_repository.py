from datetime import datetime
from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_model import CatalogAppDB
from alert_monitoring.api.driven.postgres_repository.mappers.catalog_app_db_mapper import CatalogAppDBMapper


class CatalogAppRepositoryAdapter(CatalogAppRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, catalog_app_db_mapper: CatalogAppDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.catalog_app_db_mapper = catalog_app_db_mapper
        self.logger = logger

    def save_all(self, apps: List[CatalogApp]) -> None:
        self.logger.info(f"Sincronizando {len(apps)} aplicaciones del catálogo")
        now = datetime.utcnow()

        existing: dict[str, CatalogAppDB] = {
            row.object_id: row
            for row in self.sqlalchemy_repository.query(CatalogAppDB).all()
        }

        for app in apps:
            if app.object_id in existing:
                row = existing[app.object_id]
                row.object_key = app.object_key
                row.name = app.name
                row.csw_code = app.csw_code
                row.platform = app.platform
                row.synced_at = now
            else:
                new_row = self.catalog_app_db_mapper.to_db(app)
                new_row.synced_at = now
                self.sqlalchemy_repository.add(new_row)

        self.sqlalchemy_repository.commit()

    def get_all(self, name: Optional[str] = None, csw_code: Optional[str] = None) -> List[CatalogApp]:
        self.logger.info(f"Consultando catálogo name={name} csw_code={csw_code}")
        query = self.sqlalchemy_repository.query(CatalogAppDB)

        if name:
            query = query.filter(CatalogAppDB.name.ilike(f"%{name}%"))
        if csw_code:
            query = query.filter(CatalogAppDB.csw_code.ilike(f"%{csw_code}%"))

        return self.catalog_app_db_mapper.to_domain_list(query.order_by(CatalogAppDB.name).all())
