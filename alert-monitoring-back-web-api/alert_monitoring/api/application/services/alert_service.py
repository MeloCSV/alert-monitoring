from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_rule_repository_port import DefaultAlertRuleRepositoryPort
from alert_monitoring.api.application.use_cases.get_all_alerts_use_case import GetAllAlertsUseCase
from alert_monitoring.api.application.use_cases.recompute_overrides_use_case import RecomputeOverridesUseCase
from alert_monitoring.api.application.use_cases.save_alerts_use_case import SaveAlertsUseCase
from alert_monitoring.api.driven.alertmanager_repository.adapters.alertmanager_adapter import AlertManagerAdapter
from alert_monitoring.api.driven.elastic_repository.adapters.elastic_adapter import ElasticAdapter
from alert_monitoring.api.driven.elastic_repository.mappers.elastic_mapper import ElasticMapper
from alert_monitoring.api.driven.kibana_repository.adapters.kibana_adapter import KibanaAdapter
from alert_monitoring.api.driven.prometheus_repository.adapters.prometheus_adapter import PrometheusAdapter
from alert_monitoring.api.driven.prometheus_repository.mappers.prometheus_mapper import PrometheusMapper
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.alert_override import AlertOverride
from alert_monitoring.api.domain.models.blackout import Blackout
from alert_monitoring.api.domain.models.default_alert_rule import DefaultAlertRule


class AlertService(AlertServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        alert_repository: AlertRepositoryPort,
        alert_override_repository: AlertOverrideRepositoryPort,
        default_catalog_repository: DefaultAlertRuleRepositoryPort,
        logger: LoggerSetup,
    ):
        self.alert_repository = alert_repository
        self.override_repository = alert_override_repository
        self.default_catalog_repository = default_catalog_repository
        self.save_use_case = SaveAlertsUseCase(alert_repository)
        self.get_all_use_case = GetAllAlertsUseCase(alert_repository)
        self.recompute_overrides_use_case = RecomputeOverridesUseCase(
            default_catalog_repository, alert_repository, alert_override_repository
        )
        self.prometheus_adapter = PrometheusAdapter()
        self.prometheus_mapper = PrometheusMapper()
        self.elastic_adapter = ElasticAdapter()
        self.elastic_mapper = ElasticMapper()
        self.kibana_adapter = KibanaAdapter()
        self.alertmanager_adapter = AlertManagerAdapter()
        self.logger = logger

    def sync_prometheus_alerts(self) -> int:
        self.logger.info('sync_prometheus_alerts')
        rules = self.prometheus_adapter.fetch_rules()

        catalog_rules = self.prometheus_mapper.to_catalog(rules)
        adhoc_alerts = self.prometheus_mapper.to_domain(rules)

        clusters = {r.cluster for r in catalog_rules if r.cluster and r.cluster != "unknown"}
        for cluster in clusters:
            self.default_catalog_repository.replace_for_cluster(
                cluster, [r for r in catalog_rules if r.cluster == cluster]
            )

        self.save_use_case.execute(adhoc_alerts)
        self.recompute_overrides_use_case.execute()
        return len(catalog_rules) + len(adhoc_alerts)

    def sync_elastic_alerts(self) -> int:
        self.logger.info('sync_elastic_alerts')
        raw_rules = self.kibana_adapter.fetch_rules()
        rules = self.elastic_adapter.parse_rules(raw_rules)
        alerts = self.elastic_mapper.to_domain(rules)
        self.save_use_case.execute(alerts)
        self.recompute_overrides_use_case.execute()
        return len(alerts)

    def get_all_alerts(self, filters: Optional[AlertFilter] = None) -> List[Alert]:
        self.logger.info('get_all_alerts')
        return self.get_all_use_case.execute(filters)

    def get_alert_overrides(self, solution: Optional[str] = None) -> List[AlertOverride]:
        self.logger.info(f'get_alert_overrides solution={solution}')
        return self.override_repository.get_all(solution)

    def get_active_blackouts(self) -> List[Blackout]:
        self.logger.info('get_active_blackouts')
        return self.alertmanager_adapter.fetch_active_blackouts()

    def get_default_catalog(self) -> List[DefaultAlertRule]:
        self.logger.info('get_default_catalog')
        all_rules = self.default_catalog_repository.get_all()
        seen: set = set()
        deduped: List[DefaultAlertRule] = []
        for rule in all_rules:
            key = (rule.cluster, rule.name)
            if key not in seen:
                seen.add(key)
                deduped.append(rule)
        return deduped