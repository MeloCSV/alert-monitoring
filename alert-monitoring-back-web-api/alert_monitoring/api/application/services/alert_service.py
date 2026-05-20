from typing import Dict, List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_override_repository_port import AlertOverrideRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.application.use_cases.get_all_alerts_use_case import GetAllAlertsUseCase
from alert_monitoring.api.application.use_cases.recompute_overrides_use_case import RecomputeOverridesUseCase, build_exclusion_updates
from alert_monitoring.api.application.use_cases.save_alerts_use_case import SaveAlertsUseCase
from alert_monitoring.api.driven.shared.alert_normalization import DEFAULT_ALERT_DISPLAY
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
from alert_monitoring.api.domain.models.default_alert import DefaultAlert


class AlertService(AlertServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        alert_repository: AlertRepositoryPort,
        alert_override_repository: AlertOverrideRepositoryPort,
        catalog_app_repository: CatalogAppRepositoryPort,
        default_alert_repository: DefaultAlertRepositoryPort,
        logger: LoggerSetup,
    ):
        self.alert_repository = alert_repository
        self.override_repository = alert_override_repository
        self.catalog_app_repository = catalog_app_repository
        self.default_alert_repository = default_alert_repository
        self.save_use_case = SaveAlertsUseCase(alert_repository)
        self.get_all_use_case = GetAllAlertsUseCase(alert_repository)
        self.recompute_overrides_use_case = RecomputeOverridesUseCase(
            alert_repository, alert_override_repository, default_alert_repository
        )
        self.prometheus_adapter = PrometheusAdapter()
        self.prometheus_mapper = PrometheusMapper()
        self.elastic_adapter = ElasticAdapter()
        self.elastic_mapper = ElasticMapper()
        self.kibana_adapter = KibanaAdapter()
        self.alertmanager_adapter = AlertManagerAdapter()
        self.logger = logger

    def _build_catalog_lookup(self) -> Dict[str, str]:
        return {app.name.lower(): app.name for app in self.catalog_app_repository.get_all()}

    def _normalize_solutions(self, alerts: List[Alert], catalog_lookup: Dict[str, str]) -> List[Alert]:
        for alert in alerts:
            if not alert.solution:
                continue
            canonical = catalog_lookup.get(alert.solution.lower())
            if canonical:
                alert.solution = canonical
            else:
                self.logger.warning(f"solution '{alert.solution}' not found in catalog")
        return alerts

    def _upsert_default_alerts(self, default_rules: List[Alert]) -> None:
        if not default_rules:
            return

        exclusions = build_exclusion_updates(default_rules)

        # First raw_description encountered per raw_name (annotation message from Prometheus)
        raw_descriptions: dict[str, str] = {}
        first_severity: dict[str, str] = {}
        first_channel: dict[str, str] = {}
        for alert in default_rules:
            raw_name = alert.prometheus_name
            if not raw_name:
                continue
            if raw_name not in raw_descriptions and alert.description:
                raw_descriptions[raw_name] = alert.description
            if raw_name not in first_severity and alert.severity:
                first_severity[raw_name] = alert.severity
            if raw_name not in first_channel and alert.notification_channel:
                first_channel[raw_name] = alert.notification_channel

        upsert_list: List[DefaultAlert] = []
        for raw_name, (excl_ns, incl_ns, excl_jobs) in exclusions.items():
            translation = DEFAULT_ALERT_DISPLAY.get(raw_name)
            upsert_list.append(DefaultAlert(
                raw_name=raw_name,
                display_name=translation[0] if translation else None,
                raw_description=raw_descriptions.get(raw_name),
                display_description=translation[1] if translation else None,
                severity=first_severity.get(raw_name),
                notification_channel=first_channel.get(raw_name),
                excluded_namespaces=excl_ns,
                included_namespaces=incl_ns,
                excluded_jobs=excl_jobs,
            ))

        self.default_alert_repository.upsert_batch(upsert_list)

    def sync_prometheus_alerts(self) -> int:
        self.logger.info('sync_prometheus_alerts')
        rules = self.prometheus_adapter.fetch_rules()
        alerts = self.prometheus_mapper.to_domain(rules)
        catalog_lookup = self._build_catalog_lookup()
        self._normalize_solutions(alerts, catalog_lookup)

        default_rules = [a for a in alerts if a.alert_type == "Por Defecto"]
        adhoc_alerts = [a for a in alerts if a.alert_type != "Por Defecto"]

        self.save_use_case.execute(adhoc_alerts)
        self._upsert_default_alerts(default_rules)
        self.recompute_overrides_use_case.execute()
        return len(alerts)

    def sync_elastic_alerts(self) -> int:
        self.logger.info('sync_elastic_alerts')
        raw_rules = self.kibana_adapter.fetch_rules()
        rules = self.elastic_adapter.parse_rules(raw_rules)
        alerts = self.elastic_mapper.to_domain(rules)
        catalog_lookup = self._build_catalog_lookup()
        self._normalize_solutions(alerts, catalog_lookup)
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

    def get_default_alerts(self) -> List[DefaultAlert]:
        self.logger.info('get_default_alerts')
        return self.default_alert_repository.get_all()
