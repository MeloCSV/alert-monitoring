from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_database.synchronous.datasource import DataSourceManager
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from sqlalchemy import cast, text
from sqlalchemy.dialects.postgresql import JSONB

from alert_monitoring.api.application.ports.driven.alert_api_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.driven.postgres_repository.mappers.alert_api_db_mapper import AlertApiDBMapper
from alert_monitoring.api.driven.postgres_repository.models.alert_api_model import AlertApiDB


class AlertApiRepositoryAdapter(AlertApiRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, alert_api_db_mapper: AlertApiDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.alert_api_db_mapper = alert_api_db_mapper
        self.logger = logger

    def save_all(self, rules: List[AlertApi]) -> None:
        self.logger.info(f"Guardando {len(rules)} reglas de API")
        for rule in rules:
            self.sqlalchemy_repository.add(self.alert_api_db_mapper.to_db(rule))
        self.sqlalchemy_repository.commit()

    def delete_all(self) -> None:
        deleted = self.sqlalchemy_repository.query(AlertApiDB).delete()
        self.logger.info(f"Eliminadas {deleted} reglas de API")
        self.sqlalchemy_repository.commit()

    def get_all(self, api: Optional[str] = None) -> List[AlertApi]:
        query = self.sqlalchemy_repository.query(AlertApiDB)
        if api:
            query = query.filter(cast(AlertApiDB.apis_alertadas, JSONB).contains([api]))
        return self.alert_api_db_mapper.to_domain_list(query.all())

    def get_distinct_apis(self) -> List[str]:
        rows = self.sqlalchemy_repository.execute(
            text("SELECT DISTINCT value FROM alert_api, jsonb_array_elements_text(apis_alertadas::jsonb) AS value ORDER BY value")
        )
        return [row[0] for row in rows]
