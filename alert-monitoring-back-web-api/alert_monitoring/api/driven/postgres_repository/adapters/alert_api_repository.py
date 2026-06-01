from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.application.ports.driven.alert_api_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.alert_api_model import AlertApiDB
from alert_monitoring.api.driven.postgres_repository.mappers.alert_api_db_mapper import AlertApiDBMapper


class AlertApiRepositoryAdapter(AlertApiRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, alert_api_db_mapper: AlertApiDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = alert_api_db_mapper
        self.logger = logger

    def save_all(self, alerts: List[AlertApi]) -> None:
        self.logger.info(f"Guardando {len(alerts)} alertas de API")
        for alert in alerts:
            self.sqlalchemy_repository.add(self.mapper.to_db(alert))
        self.sqlalchemy_repository.commit()

    def delete_all(self) -> None:
        deleted = self.sqlalchemy_repository.query(AlertApiDB).delete()
        self.logger.info(f"Eliminadas {deleted} alertas de API")
        self.sqlalchemy_repository.commit()

    def get_all(self, apis: Optional[List[str]] = None) -> List[AlertApi]:
        self.logger.info(f"Consultando alertas de API: apis={apis}")
        query = self.sqlalchemy_repository.query(AlertApiDB)
        if apis:
            query = query.filter(AlertApiDB.api.in_(apis))
        return self.mapper.to_domain_list(query.order_by(AlertApiDB.api, AlertApiDB.name).all())
