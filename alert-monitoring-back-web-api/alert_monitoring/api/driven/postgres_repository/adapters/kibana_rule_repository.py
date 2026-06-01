from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_database.synchronous.datasource import DataSourceManager
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driven.kibana_rule_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.domain.models.kibana_rule import AlertApi
from alert_monitoring.api.driven.postgres_repository.mappers.kibana_rule_db_mapper import AlertApiDBMapper
from alert_monitoring.api.driven.postgres_repository.models.kibana_rule_model import AlertApiDB


class AlertApiRepositoryAdapter(AlertApiRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, alert_api_db_mapper: AlertApiDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.alert_api_db_mapper = alert_api_db_mapper
        self.logger = logger

    def save_all(self, rules: List[AlertApi]) -> None:
        self.logger.info(f"Guardando {len(rules)} reglas de API")
        for rule in rules:
            self.sqlalchemy_repository.add(self.alert_api_db_mapper.to_db(rule))
        self.sqlalchemy_repository.commit()

    def delete_all(self) -> None:
        deleted = self.sqlalchemy_repository.query(AlertApiDB).delete()
        self.logger.info(f"Eliminadas {deleted} reglas de API")
        self.sqlalchemy_repository.commit()

    def get_all(self, api: Optional[str] = None) -> List[AlertApi]:
        rules_db = self.sqlalchemy_repository.query(AlertApiDB).all()

        if api:
            api_lower = api.lower()
            rules_db = [r for r in rules_db if r.apis_alertadas and any(a.lower() == api_lower for a in r.apis_alertadas)]

        return self.alert_api_db_mapper.to_domain_list(rules_db)

    def get_distinct_apis(self) -> List[str]:
        rules_db = self.sqlalchemy_repository.query(AlertApiDB).all()
        apis: set[str] = set()
        for r in rules_db:
            for api in (r.apis_alertadas or []):
                apis.add(api)
        return sorted(apis)
