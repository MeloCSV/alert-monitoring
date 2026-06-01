from typing import List

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi
from alert_monitoring.api.application.ports.driven.default_alert_api_repository_port import DefaultAlertApiRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.default_alert_api_model import DefaultAlertApiDB
from alert_monitoring.api.driven.postgres_repository.mappers.default_alert_api_db_mapper import DefaultAlertApiDBMapper


class DefaultAlertApiRepositoryAdapter(DefaultAlertApiRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, default_alert_api_db_mapper: DefaultAlertApiDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = default_alert_api_db_mapper
        self.logger = logger

    def get_all(self) -> List[DefaultAlertApi]:
        rows = self.sqlalchemy_repository.query(DefaultAlertApiDB).order_by(DefaultAlertApiDB.id).all()
        return self.mapper.to_domain_list(rows)

    def upsert_batch(self, alerts: List[DefaultAlertApi]) -> None:
        self.logger.info(f"Upsert de {len(alerts)} alertas por defecto en default_alert_api")
        for alert in alerts:
            existing = (
                self.sqlalchemy_repository.query(DefaultAlertApiDB)
                .filter(DefaultAlertApiDB.raw_name == alert.raw_name)
                .first()
            )
            if existing is None:
                self.sqlalchemy_repository.add(DefaultAlertApiDB(
                    raw_name=alert.raw_name,
                    display_name=alert.display_name or alert.raw_name,
                    raw_description=alert.raw_description,
                    display_description=alert.display_description,
                    severity=alert.severity,
                    notification_channel=alert.notification_channel,
                    excluded_apis=alert.excluded_apis,
                ))
            else:
                existing.raw_description = alert.raw_description
                existing.excluded_apis = alert.excluded_apis
                if alert.severity:
                    existing.severity = alert.severity
                if alert.notification_channel:
                    existing.notification_channel = alert.notification_channel
                if existing.display_name is None:
                    existing.display_name = alert.display_name or alert.raw_name
                if existing.display_description is None and alert.display_description:
                    existing.display_description = alert.display_description
        self.sqlalchemy_repository.commit()
