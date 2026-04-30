from typing import List

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.alert_model import AlertDB
from alert_monitoring.api.driven.postgres_repository.mappers.alert_db_mapper import AlertDBMapper


class AlertRepositoryAdapter(AlertRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, alert_db_mapper: AlertDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.alert_db_mapper = alert_db_mapper
        self.logger = logger

    def save_all(self, alerts: List[Alert]) -> None:
        self.logger.info(f"Guardando {len(alerts)} alertas")
        for alert in alerts:
            alert_db = self.alert_db_mapper.to_db(alert)
            self.sqlalchemy_repository.add(alert_db)
        self.sqlalchemy_repository.commit()

    def get_all(self) -> List[Alert]:
        self.logger.info("Consultando todas las alertas")
        alerts_db = self.sqlalchemy_repository.query(AlertDB).all()
        return self.alert_db_mapper.to_domain_list(alerts_db)