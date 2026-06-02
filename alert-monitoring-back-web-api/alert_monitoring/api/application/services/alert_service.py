import re
from typing import Dict, List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_api_repository_port import CatalogAppApiRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_api_repository_port import DefaultAlertApiRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_api_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.application.use_cases.get_all_alerts_use_case import GetAllAlertsUseCase
from alert_monitoring.api.application.use_cases.get_api_solution_view_use_case import GetApiSolutionViewUseCase
from alert_monitoring.api.application.use_cases.get_solution_view_use_case import GetSolutionViewUseCase
from alert_monitoring.api.application.use_cases.save_alerts_use_case import SaveAlertsUseCase
from alert_monitoring.api.application.services.catalog_lookup import build_catalog_lookup
from alert_monitoring.api.driven.shared.alert_normalization import DEFAULT_ALERT_DISPLAY, build_exclusion_updates
from alert_monitoring.api.driven.alertmanager_repository.adapters.alertmanager_adapter import AlertManagerAdapter
from alert_monitoring.api.driven.elastic_repository.adapters.elastic_adapter import ElasticAdapter
from alert_monitoring.api.driven.elastic_repository.mappers.elastic_mapper import ElasticMapper
from alert_monitoring.api.driven.kibana_repository.adapters.kibana_adapter import KibanaAdapter
from alert_monitoring.api.driven.prometheus_repository.adapters.prometheus_adapter import PrometheusAdapter
from alert_monitoring.api.driven.prometheus_repository.mappers.prometheus_mapper import PrometheusMapper, is_default_rule
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.blackout import Blackout
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.solution_view import SolutionView
from alert_monitoring.api.domain.models.api_solution_view import ApiSolutionView


class AlertService(AlertServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        alert_repository: AlertRepositoryPort,
        alert_api_repository: AlertApiRepositoryPort,
        catalog_app_repository: CatalogAppRepositoryPort,
        catalog_app_api_repository: CatalogAppApiRepositoryPort,
        default_alert_repository: DefaultAlertRepositoryPort,
        default_alert_api_repository: DefaultAlertApiRepositoryPort,
        logger: LoggerSetup,
    ):
        self.alert_repository = alert_repository
        self.alert_api_repository = alert_api_repository
        self.catalog_app_repository = catalog_app_repository
        self.catalog_app_api_repository = catalog_app_api_repository
        self.default_alert_repository = default_alert_repository
        self.default_alert_api_repository = default_alert_api_repository
        self.save_use_case = SaveAlertsUseCase(alert_repository)
        self.get_all_use_case = GetAllAlertsUseCase(alert_repository)
        self.get_solution_view_use_case = GetSolutionViewUseCase(
            alert_repository, default_alert_repository
        )
        self.get_api_solution_view_use_case = GetApiSolutionViewUseCase(
            catalog_app_api_repository, default_alert_api_repository, alert_api_repository
        )
        self.prometheus_adapter = PrometheusAdapter()
        self.prometheus_mapper = PrometheusMapper()
        self.elastic_adapter = ElasticAdapter()
        self.elastic_mapper = ElasticMapper()
        self.kibana_adapter = KibanaAdapter()
        self.alertmanager_adapter = AlertManagerAdapter()
        self.logger = logger

    def _build_catalog_lookup(self) -> Dict[str, str]:
        return build_catalog_lookup(self.catalog_app_repository)

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

    def _upsert_default_alerts(self, default_rules) -> None:
        if not default_rules:
            return

        exclusions = build_exclusion_updates(default_rules)

        raw_descriptions: dict[str, str] = {}
        first_severity: dict[str, str] = {}
        first_channel: dict[str, str] = {}
        for rule in default_rules:
            raw_name = rule.alert.split()[0] if rule.alert else None
            if not raw_name:
                continue
            if raw_name not in raw_descriptions:
                raw_descriptions[raw_name] = rule.annotations.get("message", "")
            if raw_name not in first_severity:
                first_severity[raw_name] = rule.labels.get("severity", "")
            if raw_name not in first_channel:
                first_channel[raw_name] = self.prometheus_mapper._infer_channel(rule.labels) or ""

        upsert_list: List[DefaultAlert] = []
        for raw_name, (excl_ns, incl_ns, excl_jobs) in exclusions.items():
            translation = DEFAULT_ALERT_DISPLAY.get(raw_name)
            upsert_list.append(DefaultAlert(
                raw_name=raw_name,
                display_name=translation[0] if translation else raw_name,
                raw_description=raw_descriptions.get(raw_name) or None,
                display_description=translation[1] if translation else None,
                severity=first_severity.get(raw_name) or None,
                notification_channel=first_channel.get(raw_name) or None,
                excluded_namespaces=excl_ns,
                included_namespaces=incl_ns,
                excluded_jobs=excl_jobs,
            ))

        self.default_alert_repository.upsert_batch(upsert_list)

    def sync_prometheus_alerts(self) -> int:
        self.logger.info('sync_prometheus_alerts')
        rules = self.prometheus_adapter.fetch_rules()
        default_raw_rules = [r for r in rules if is_default_rule(r)]
        adhoc_alerts = [a for a in self.prometheus_mapper.to_domain(rules) if a.alert_type != "Por Defecto"]
        catalog_lookup = self._build_catalog_lookup()
        self._normalize_solutions(adhoc_alerts, catalog_lookup)

        self.alert_repository.delete_by_source_tool("Prometheus")
        self.save_use_case.execute(adhoc_alerts)
        self._upsert_default_alerts(default_raw_rules)
        return len(rules)

    def sync_elastic_alerts(self) -> int:
        self.logger.info('sync_elastic_alerts')
        raw_rules = self.kibana_adapter.fetch_rules()
        rules = self.elastic_adapter.parse_rules(raw_rules)
        alerts = self.elastic_mapper.to_domain(rules)
        catalog_lookup = self._build_catalog_lookup()
        self._normalize_solutions(alerts, catalog_lookup)
        self.alert_repository.delete_by_source_tool("Elastic")
        self.save_use_case.execute(alerts)
        return len(alerts)

    def get_all_alerts(self, filters: Optional[AlertFilter] = None) -> List[Alert]:
        self.logger.info('get_all_alerts')
        return self.get_all_use_case.execute(filters)

    _APP_MATCHER_FIELDS = frozenset({
        'namespace', 'solucion', 'solution', 'exported_namespace',
        'backend_target_name', 'deployment', 'replicaset', 'cronjob', 'pod',
    })

    def _blackout_matches_solution(self, blackout: Blackout, solution: str) -> bool:
        sol = solution.lower()
        variants = {sol, f"{sol}-back", f"{sol}-front"}
        for matcher in blackout.matchers:
            if matcher.name not in self._APP_MATCHER_FIELDS or not matcher.is_equal:
                continue
            if matcher.is_regex:
                try:
                    pattern = re.compile(matcher.value, re.IGNORECASE)
                    if any(pattern.search(v) for v in variants):
                        return True
                except re.error:
                    continue
            else:
                val = matcher.value.lower()
                if val in variants or any(val.startswith(f"{v}-") for v in variants):
                    return True
        return False

    def get_active_blackouts(self, solution: Optional[str] = None) -> List[Blackout]:
        self.logger.info(f'get_active_blackouts solution={solution}')
        blackouts = self.alertmanager_adapter.fetch_active_blackouts()
        if solution:
            blackouts = [b for b in blackouts if self._blackout_matches_solution(b, solution)]
        return blackouts

    def get_default_alerts(self) -> List[DefaultAlert]:
        self.logger.info('get_default_alerts')
        return self.default_alert_repository.get_all()

    def get_solution_view(self, solution: str) -> SolutionView:
        self.logger.info(f'get_solution_view solution={solution}')
        return self.get_solution_view_use_case.execute(solution)

    def get_api_solution_view(self, app: str) -> ApiSolutionView:
        self.logger.info(f'get_api_solution_view app={app}')
        return self.get_api_solution_view_use_case.execute(app)
