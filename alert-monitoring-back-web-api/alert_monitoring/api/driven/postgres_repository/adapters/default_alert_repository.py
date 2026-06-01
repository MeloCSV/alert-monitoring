from typing import List

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.default_alert_model import DefaultAlertDB
from alert_monitoring.api.driven.postgres_repository.mappers.default_alert_db_mapper import DefaultAlertDBMapper
from alert_monitoring.api.driven.postgres_repository.sync_helpers import upsert_preserving_display


class DefaultAlertRepositoryAdapter(DefaultAlertRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, default_alert_db_mapper: DefaultAlertDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = default_alert_db_mapper
        self.logger = logger

    def get_all(self) -> List[DefaultAlert]:
        rows = self.sqlalchemy_repository.query(DefaultAlertDB).order_by(DefaultAlertDB.id).all()
        return self.mapper.to_domain_list(rows)

    def upsert_batch(self, alerts: List[DefaultAlert]) -> None:
        self.logger.info(f"Upsert de {len(alerts)} alertas por defecto en default_alerts")
        upsert_preserving_display(
            self.sqlalchemy_repository,
            DefaultAlertDB,
            alerts,
            owned_fields=lambda alert: {
                # Campos cuya fuente de verdad es Prometheus
                "raw_description": alert.raw_description,
                "excluded_namespaces": alert.excluded_namespaces,
                "included_namespaces": alert.included_namespaces,
                "excluded_jobs": alert.excluded_jobs,
            },
        )
