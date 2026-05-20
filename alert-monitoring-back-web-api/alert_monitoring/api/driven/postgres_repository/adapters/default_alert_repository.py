from typing import List

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

    def upsert_batch(self, alerts: List[DefaultAlert]) -> None:
        self.logger.info(f"Upsert de {len(alerts)} alertas por defecto en default_alerts")
        for alert in alerts:
            existing = (
                self.sqlalchemy_repository.query(DefaultAlertDB)
                .filter(DefaultAlertDB.raw_name == alert.raw_name)
                .first()
            )
            if existing is None:
                self.sqlalchemy_repository.add(DefaultAlertDB(
                    raw_name=alert.raw_name,
                    display_name=alert.display_name or alert.raw_name,
                    raw_description=alert.raw_description,
                    display_description=alert.display_description,
                    severity=alert.severity,
                    notification_channel=alert.notification_channel,
                    excluded_namespaces=alert.excluded_namespaces,
                    included_namespaces=alert.included_namespaces,
                    excluded_jobs=alert.excluded_jobs,
                ))
            else:
                # Always update what Prometheus owns
                existing.raw_description = alert.raw_description
                existing.excluded_namespaces = alert.excluded_namespaces
                existing.included_namespaces = alert.included_namespaces
                existing.excluded_jobs = alert.excluded_jobs
                if alert.severity:
                    existing.severity = alert.severity
                if alert.notification_channel:
                    existing.notification_channel = alert.notification_channel
                # Only fill display fields if not already set (preserve manual edits)
                if existing.display_name is None:
                    existing.display_name = alert.display_name or alert.raw_name
                if existing.display_description is None and alert.display_description:
                    existing.display_description = alert.display_description
        self.sqlalchemy_repository.commit()
