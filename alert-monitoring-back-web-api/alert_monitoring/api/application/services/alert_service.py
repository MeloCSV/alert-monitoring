from typing import List

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.use_cases.save_alerts_use_case import SaveAlertsUseCase
from alert_monitoring.api.application.use_cases.save_elastic_alerts_use_case import SaveElasticAlertsUseCase
from alert_monitoring.api.application.use_cases.get_all_alerts_use_case import GetAllAlertsUseCase
from alert_monitoring.api.driven.prometheus_repository.adapters.prometheus_adapter import PrometheusAdapter
from alert_monitoring.api.driven.prometheus_repository.mappers.prometheus_mapper import PrometheusMapper
from alert_monitoring.api.driven.elastic_repository.adapters.elastic_adapter import ElasticAdapter
from alert_monitoring.api.driven.elastic_repository.mappers.elastic_mapper import ElasticMapper
from alert_monitoring.api.domain.models.alert import Alert


class AlertService(AlertServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(self, alert_repository: AlertRepositoryPort, logger: LoggerSetup):
        self.save_use_case = SaveAlertsUseCase(alert_repository)
        self.save_elastic_use_case = SaveElasticAlertsUseCase(alert_repository)
        self.get_all_use_case = GetAllAlertsUseCase(alert_repository)
        self.prometheus_adapter = PrometheusAdapter()
        self.prometheus_mapper = PrometheusMapper()
        self.elastic_adapter = ElasticAdapter()
        self.elastic_mapper = ElasticMapper()
        self.logger = logger

    def save_alerts(self, yaml_content: str) -> None:
        self.logger.info('save_alerts')
        rules = self.prometheus_adapter.load_rules(yaml_content)
        alerts = self.prometheus_mapper.to_domain(rules)
        self.save_use_case.execute(alerts)

    def save_elastic_alerts(self, json_content: str) -> None:
        self.logger.info('save_elastic_alerts')
        rules = self.elastic_adapter.load_rules(json_content)
        alerts = self.elastic_mapper.to_domain(rules)
        self.save_elastic_use_case.execute(alerts)

    def get_all_alerts(self) -> List[Alert]:
        self.logger.info('get_all_alerts')
        return self.get_all_use_case.execute()