from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driven.kibana_rule_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.application.ports.driving.kibana_rule_service_port import AlertApiServicePort
from alert_monitoring.api.domain.models.kibana_rule import AlertApi
from alert_monitoring.api.driven.kibana_repository.adapters.kibana_adapter import KibanaAdapter
from alert_monitoring.api.driven.kibana_repository.mappers.kibana_rule_mapper import KibanaRuleMapper


class AlertApiService(AlertApiServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        alert_api_repository: AlertApiRepositoryPort,
        logger: LoggerSetup,
    ):
        self.alert_api_repository = alert_api_repository
        self.kibana_adapter = KibanaAdapter()
        self.kibana_rule_mapper = KibanaRuleMapper()
        self.logger = logger

    def sync_kibana_rules(self) -> int:
        self.logger.info("sync_kibana_rules")
        rules: List[AlertApi] = []
        for config, raw_rules in self.kibana_adapter.fetch_rules_by_config():
            rules.extend(self.kibana_rule_mapper.to_domain(raw_rules, config))

        self.alert_api_repository.delete_all()
        self.alert_api_repository.save_all(rules)
        return len(rules)

    def get_rules(self, api: Optional[str] = None) -> List[AlertApi]:
        self.logger.info(f"get_rules api={api}")
        return self.alert_api_repository.get_all(api=api)

    def get_apis(self) -> List[str]:
        self.logger.info("get_apis")
        return self.alert_api_repository.get_distinct_apis()
