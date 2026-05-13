from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.alert_override import AlertOverride
from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.alert_override_model import AlertOverrideDB
from alert_monitoring.api.driven.postgres_repository.mappers.alert_override_db_mapper import AlertOverrideDBMapper


class AlertOverrideRepositoryAdapter(AlertOverrideRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, alert_override_db_mapper: AlertOverrideDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = alert_override_db_mapper
        self.logger = logger

    def replace_all(self, overrides: List[AlertOverride]) -> None:
        self.logger.info(f"Reescribiendo {len(overrides)} overrides de alerta")
        self.sqlalchemy_repository.query(AlertOverrideDB).delete()
        for override in overrides:
            self.sqlalchemy_repository.add(self.mapper.to_db(override))
        self.sqlalchemy_repository.commit()

    def get_all(self, microservice: Optional[str] = None) -> List[AlertOverride]:
        query = self.sqlalchemy_repository.query(AlertOverrideDB)
        if microservice:
            query = query.filter(AlertOverrideDB.microservice == microservice)
        return self.mapper.to_domain_list(query.all())
