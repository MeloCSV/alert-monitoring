from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driven.alert_api_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_api_repository_port import DefaultAlertApiRepositoryPort
from alert_monitoring.api.application.ports.driving.alert_api_service_port import AlertApiServicePort
from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.driven.kibana_repository.adapters.kibana_adapter import KibanaAdapter
from alert_monitoring.api.driven.kibana_repository.mappers.kibana_rule_mapper import KibanaRuleMapper


class AlertApiService(AlertApiServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        alert_api_repository: AlertApiRepositoryPort,
        default_alert_api_repository: DefaultAlertApiRepositoryPort,
        logger: LoggerSetup,
    ):
        self.alert_api_repository = alert_api_repository
        self.default_alert_api_repository = default_alert_api_repository
        self.kibana_adapter = KibanaAdapter()
        self.kibana_rule_mapper = KibanaRuleMapper()
        self.logger = logger

    def sync_alert_apis(self) -> int:
        self.logger.info("sync_alert_apis")
        default_alerts = []
        adhoc_rules = []

        for config, raw_rules in self.kibana_adapter.fetch_rules_by_config():
            defaults, adhoc = self.kibana_rule_mapper.to_domain_split(raw_rules, config)
            default_alerts.extend(defaults)
            adhoc_rules.extend(adhoc)

        self.default_alert_api_repository.upsert_batch(default_alerts)
        self.default_alert_api_repository.delete_where_not_in([d.raw_name for d in default_alerts])
        self.alert_api_repository.delete_all()
        self.alert_api_repository.save_all(adhoc_rules)

        self.logger.info(
            f"sync_alert_apis: {len(default_alerts)} reglas globales en default_alert_api, "
            f"{len(adhoc_rules)} reglas ad-hoc en alert_api"
        )
        return len(default_alerts) + len(adhoc_rules)

    def get_alert_apis(self, api: Optional[str] = None) -> List[AlertApi]:
        self.logger.info(f"get_alert_apis api={api}")
        return self.alert_api_repository.get_all(api=api)

    def get_apis(self) -> List[str]:
        self.logger.info("get_apis")
        return self.alert_api_repository.get_distinct_apis()
