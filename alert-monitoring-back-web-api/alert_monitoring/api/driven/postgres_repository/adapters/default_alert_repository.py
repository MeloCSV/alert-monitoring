from typing import Dict, List, Tuple

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.default_alert_model import DefaultAlertDB
from alert_monitoring.api.driven.postgres_repository.mappers.default_alert_db_mapper import DefaultAlertDBMapper


class DefaultAlertRepositoryAdapter(DefaultAlertRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, default_alert_db_mapper: DefaultAlertDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = default_alert_db_mapper
        self.logger = logger

    def get_all(self) -> List[DefaultAlert]:
        rows = self.sqlalchemy_repository.query(DefaultAlertDB).order_by(DefaultAlertDB.id).all()
        return self.mapper.to_domain_list(rows)

    def replace_exclusions(self, updates: Dict[str, Tuple[List[str], List[str], List[str]]]) -> None:
        self.logger.info(f"Actualizando patrones de exclusión para {len(updates)} alertas por defecto")
        for raw_name, (excl_ns, incl_ns, excl_jobs) in updates.items():
            row = self.sqlalchemy_repository.query(DefaultAlertDB).filter(DefaultAlertDB.raw_name == raw_name).first()
            if row is None:
                continue
            row.excluded_namespaces = sorted(excl_ns)
            row.included_namespaces = sorted(incl_ns)
            row.excluded_jobs = sorted(excl_jobs)
        self.sqlalchemy_repository.commit()

    def update_raw_description(self, raw_name: str, raw_description: str) -> None:
        row = self.sqlalchemy_repository.query(DefaultAlertDB).filter(DefaultAlertDB.raw_name == raw_name).first()
        if row is not None and row.raw_description is None:
            row.raw_description = raw_description
            self.sqlalchemy_repository.commit()
