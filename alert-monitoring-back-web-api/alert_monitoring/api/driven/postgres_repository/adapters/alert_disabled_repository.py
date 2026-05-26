from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.alert_disabled import AlertDisabled
from alert_monitoring.api.application.ports.driven.alert_disabled_repository_port import AlertDisabledRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.alert_disabled_model import AlertDisabledDB
from alert_monitoring.api.driven.postgres_repository.mappers.alert_disabled_db_mapper import AlertDisabledDBMapper


class AlertDisabledRepositoryAdapter(AlertDisabledRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, alert_disabled_db_mapper: AlertDisabledDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = alert_disabled_db_mapper
        self.logger = logger

    def replace_all(self, disabled_alerts: List[AlertDisabled]) -> None:
        self.logger.info(f"Reescribiendo {len(disabled_alerts)} alertas deshabilitadas")
        self.sqlalchemy_repository.query(AlertDisabledDB).delete()
        for disabled in disabled_alerts:
            self.sqlalchemy_repository.add(self.mapper.to_db(disabled))
        self.sqlalchemy_repository.commit()

    def get_all(self, solution: Optional[str] = None) -> List[AlertDisabled]:
        query = self.sqlalchemy_repository.query(AlertDisabledDB)
        if solution:
            query = query.filter(AlertDisabledDB.solution == solution)
        return self.mapper.to_domain_list(query.all())
