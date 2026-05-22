from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_database.synchronous.datasource import DataSourceManager
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driven.kibana_rule_repository_port import KibanaRuleRepositoryPort
from alert_monitoring.api.domain.models.kibana_rule import KibanaRule
from alert_monitoring.api.driven.postgres_repository.mappers.kibana_rule_db_mapper import KibanaRuleDBMapper
from alert_monitoring.api.driven.postgres_repository.models.kibana_rule_model import KibanaRuleDB


class KibanaRuleRepositoryAdapter(KibanaRuleRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, kibana_rule_db_mapper: KibanaRuleDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.kibana_rule_db_mapper = kibana_rule_db_mapper
        self.logger = logger

    def save_all(self, rules: List[KibanaRule]) -> None:
        self.logger.info(f"Guardando {len(rules)} reglas de Kibana")
        for rule in rules:
            self.sqlalchemy_repository.add(self.kibana_rule_db_mapper.to_db(rule))
        self.sqlalchemy_repository.commit()

    def delete_all(self) -> None:
        deleted = self.sqlalchemy_repository.query(KibanaRuleDB).delete()
        self.logger.info(f"Eliminadas {deleted} reglas de Kibana")
        self.sqlalchemy_repository.commit()

    def get_all(self, api: Optional[str] = None, is_global: Optional[bool] = None) -> List[KibanaRule]:
        query = self.sqlalchemy_repository.query(KibanaRuleDB)
        if is_global is not None:
            query = query.filter(KibanaRuleDB.is_global == is_global)

        rules_db = query.all()

        if api:
            api_lower = api.lower()
            rules_db = [r for r in rules_db if r.apis and any(a.lower() == api_lower for a in r.apis)]

        return self.kibana_rule_db_mapper.to_domain_list(rules_db)

    def get_distinct_apis(self) -> List[str]:
        rules_db = self.sqlalchemy_repository.query(KibanaRuleDB).filter(KibanaRuleDB.is_global == False).all()
        apis: set[str] = set()
        for r in rules_db:
            for api in (r.apis or []):
                apis.add(api)
        return sorted(apis)
