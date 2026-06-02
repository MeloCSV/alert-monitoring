from typing import List,Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
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

    def delete_by_source_tool(self, source_tool: str) -> None:
        deleted = self.sqlalchemy_repository.query(AlertDB).filter(AlertDB.source_tool == source_tool).delete()
        self.logger.info(f"Eliminadas {deleted} alertas de source_tool='{source_tool}'")
        self.sqlalchemy_repository.commit()

    def get_all(self, filters: Optional[AlertFilter] = None) -> List[Alert]:
        self.logger.info(f"Consultando alertas con filtros: {filters}")
        query = self.sqlalchemy_repository.query(AlertDB)

        if filters is not None:
            if filters.name:
                query = query.filter(AlertDB.name.ilike(f"%{filters.name}%"))
            if filters.source_tool:
                query = query.filter(AlertDB.source_tool == filters.source_tool)
            if filters.severity:
                query = query.filter(AlertDB.severity == filters.severity)
            if filters.microservice:
                query = query.filter(AlertDB.microservice.ilike(f"%{filters.microservice}%"))
            if filters.solution:
                query = query.filter(AlertDB.solution == filters.solution)

        alerts_db = query.all()

        if filters is not None and filters.environments:
            wanted = set(filters.environments)
            alerts_db = [
                a for a in alerts_db
                if a.environments and wanted.intersection(a.environments)
            ]

        return self.alert_db_mapper.to_domain_list(alerts_db)