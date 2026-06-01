from typing import List

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi
from alert_monitoring.api.application.ports.driven.default_alert_api_repository_port import DefaultAlertApiRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.default_alert_api_model import DefaultAlertApiDB
from alert_monitoring.api.driven.postgres_repository.mappers.default_alert_api_db_mapper import DefaultAlertApiDBMapper
from alert_monitoring.api.driven.postgres_repository.sync_helpers import upsert_preserving_display


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
        upsert_preserving_display(
            self.sqlalchemy_repository,
            DefaultAlertApiDB,
            alerts,
            owned_fields=lambda alert: {
                # Campos cuya fuente de verdad es Kibana
                "raw_description": alert.raw_description,
                "excluded_apis": alert.excluded_apis,
            },
        )

    def delete_where_not_in(self, raw_names: List[str]) -> None:
        self.logger.info(f"Eliminando reglas globales obsoletas (fuera de {len(raw_names)} activas)")
        query = self.sqlalchemy_repository.query(DefaultAlertApiDB)
        if raw_names:
            query = query.filter(DefaultAlertApiDB.raw_name.notin_(raw_names))
        query.delete(synchronize_session=False)
        self.sqlalchemy_repository.commit()
