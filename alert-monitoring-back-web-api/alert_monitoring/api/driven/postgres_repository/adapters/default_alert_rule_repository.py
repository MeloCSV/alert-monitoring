from typing import List
from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.default_alert_rule import DefaultAlertRule
from alert_monitoring.api.application.ports.driven.default_alert_rule_repository_port import DefaultAlertRuleRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.default_alert_rule_model import DefaultAlertRuleDB
from alert_monitoring.api.driven.postgres_repository.mappers.default_alert_rule_db_mapper import DefaultAlertRuleDBMapper

class DefaultAlertRuleRepository(DefaultAlertRuleRepositoryPort):
    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, mapper: DefaultAlertRuleDBMapper, logger: LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.mapper = mapper
        self.logger = logger

    def replace_for_cluster(self, cluster: str, rules: List[DefaultAlertRule]) -> None:
        self.logger.info(f"Reemplazando catálogo de defaults para cluster '{cluster}': {len(rules)} reglas")
        self.sqlalchemy_repository.query(DefaultAlertRuleDB).filter(DefaultAlertRuleDB.cluster == cluster).delete()
        for rule in rules:
            self.sqlalchemy_repository.add(self.mapper.to_db(rule))
        self.sqlalchemy_repository.commit()

    def get_all(self) -> List[DefaultAlertRule]:
        return self.mapper.to_domain_list(self.sqlalchemy_repository.query(DefaultAlertRuleDB).all())
