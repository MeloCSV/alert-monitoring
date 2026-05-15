from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.application.use_cases.get_all_alerts_use_case import GetAllAlertsUseCase
from alert_monitoring.api.application.use_cases.recompute_overrides_use_case import RecomputeOverridesUseCase
from alert_monitoring.api.application.use_cases.save_alerts_use_case import SaveAlertsUseCase
from alert_monitoring.api.driven.alertmanager_repository.adapters.alertmanager_adapter import AlertManagerAdapter
from alert_monitoring.api.driven.elastic_repository.adapters.elastic_adapter import ElasticAdapter
from alert_monitoring.api.driven.elastic_repository.mappers.elastic_mapper import ElasticMapper
from alert_monitoring.api.driven.prometheus_repository.adapters.prometheus_adapter import PrometheusAdapter
from alert_monitoring.api.driven.prometheus_repository.mappers.prometheus_mapper import PrometheusMapper
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.alert_override import AlertOverride
from alert_monitoring.api.domain.models.blackout import Blackout


class AlertService(AlertServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(self, alert_repository: AlertRepositoryPort, alert_override_repository: AlertOverrideRepositoryPort, logger: LoggerSetup):
        self.alert_repository = alert_repository
        self.override_repository = alert_override_repository
        self.save_use_case = SaveAlertsUseCase(alert_repository)
        self.get_all_use_case = GetAllAlertsUseCase(alert_repository)
        self.recompute_overrides_use_case = RecomputeOverridesUseCase(alert_repository, alert_override_repository)
        self.prometheus_adapter = PrometheusAdapter()
        self.prometheus_mapper = PrometheusMapper()
        self.elastic_adapter = ElasticAdapter()
        self.elastic_mapper = ElasticMapper()
        self.alertmanager_adapter = AlertManagerAdapter()
        self.logger = logger

    def sync_prometheus_alerts(self) -> int:
        self.logger.info('sync_prometheus_alerts')
        rules = self.prometheus_adapter.fetch_rules()
        alerts = self.prometheus_mapper.to_domain(rules)
        self.save_use_case.execute(alerts)
        self.recompute_overrides_use_case.execute()
        return len(alerts)

    def save_elastic_alerts(self, json_content: str) -> None:
        self.logger.info('save_elastic_alerts')
        rules = self.elastic_adapter.load_rules(json_content)
        alerts = self.elastic_mapper.to_domain(rules)
        self.save_use_case.execute(alerts)
        self.recompute_overrides_use_case.execute()

    def get_all_alerts(self, filters: Optional[AlertFilter] = None) -> List[Alert]:
        self.logger.info('get_all_alerts')
        return self.get_all_use_case.execute(filters)

    def get_alert_overrides(self, solution: Optional[str] = None) -> List[AlertOverride]:
        self.logger.info(f'get_alert_overrides solution={solution}')
        return self.override_repository.get_all(solution)

    def get_active_blackouts(self) -> List[Blackout]:
        self.logger.info('get_active_blackouts')
        return self.alertmanager_adapter.fetch_active_blackouts()