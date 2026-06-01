from datetime import datetime
from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_database.synchronous.datasource import DataSourceManager
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driven.catalog_app_api_repository_port import CatalogAppApiRepositoryPort
from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi
from alert_monitoring.api.driven.postgres_repository.mappers.catalog_app_api_db_mapper import CatalogAppApiDBMapper
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_api_model import CatalogAppApiDB


class CatalogAppApiRepositoryAdapter(CatalogAppApiRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, catalog_app_api_db_mapper: CatalogAppApiDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = catalog_app_api_db_mapper
        self.logger = logger

    def replace_all(self, items: List[CatalogAppApi]) -> None:
        self.logger.info(f"Sincronizando {len(items)} entradas de catalog_app_api")
        now = datetime.utcnow()

        existing: dict[str, CatalogAppApiDB] = {
            row.microservice: row
            for row in self.sqlalchemy_repository.query(CatalogAppApiDB).all()
        }
        incoming_micros = {item.microservice for item in items}

        for item in items:
            if item.microservice in existing:
                row = existing[item.microservice]
                row.app = item.app
                row.apis = item.apis
                row.synced_at = now
            else:
                new_row = self.mapper.to_db(item)
                new_row.synced_at = now
                self.sqlalchemy_repository.add(new_row)

        for microservice, row in existing.items():
            if microservice not in incoming_micros:
                self.sqlalchemy_repository.delete(row)

        self.sqlalchemy_repository.commit()

    def get_all(self, app: Optional[str] = None) -> List[CatalogAppApi]:
        query = self.sqlalchemy_repository.query(CatalogAppApiDB)
        if app:
            query = query.filter(CatalogAppApiDB.app.ilike(f"%{app}%"))
        return self.mapper.to_domain_list(query.order_by(CatalogAppApiDB.app, CatalogAppApiDB.microservice).all())
