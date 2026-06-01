from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.alert_api_disabled import AlertApiDisabled
from alert_monitoring.api.application.ports.driven.alert_api_disabled_repository_port import AlertApiDisabledRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.alert_api_disabled_model import AlertApiDisabledDB
from alert_monitoring.api.driven.postgres_repository.mappers.alert_api_disabled_db_mapper import AlertApiDisabledDBMapper


class AlertApiDisabledRepositoryAdapter(AlertApiDisabledRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, alert_api_disabled_db_mapper: AlertApiDisabledDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = alert_api_disabled_db_mapper
        self.logger = logger

    def replace_all(self, disabled_alerts: List[AlertApiDisabled]) -> None:
        self.logger.info(f"Reescribiendo {len(disabled_alerts)} alertas de API deshabilitadas")
        self.sqlalchemy_repository.query(AlertApiDisabledDB).delete()
        for disabled in disabled_alerts:
            self.sqlalchemy_repository.add(self.mapper.to_db(disabled))
        self.sqlalchemy_repository.commit()

    def get_all(self, api: Optional[str] = None) -> List[AlertApiDisabled]:
        query = self.sqlalchemy_repository.query(AlertApiDisabledDB)
        if api:
            query = query.filter(AlertApiDisabledDB.api == api)
        return self.mapper.to_domain_list(query.all())
