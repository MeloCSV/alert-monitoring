import re
from typing import Dict, List, Set

from alert_monitoring.api.application.ports.driven.catalog_app_api_repository_port import CatalogAppApiRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_api_repository_port import DefaultAlertApiRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_api_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi
from alert_monitoring.api.domain.models.api_solution_view import ApiSolutionView, DefaultAlertApiView

_VERSION_SUFFIX = re.compile(r'\s+v\d+$')


def _strip_version(api: str) -> str:
    return _VERSION_SUFFIX.sub('', api)


class GetApiSolutionViewUseCase:
    def __init__(
        self,
        catalog_app_api_repository: CatalogAppApiRepositoryPort,
        default_alert_api_repository: DefaultAlertApiRepositoryPort,
        alert_api_repository: AlertApiRepositoryPort,
    ):
        self.catalog_app_api_repository = catalog_app_api_repository
        self.default_alert_api_repository = default_alert_api_repository
        self.alert_api_repository = alert_api_repository

    def execute(self, app: str) -> ApiSolutionView:
        catalog_entries = self.catalog_app_api_repository.get_all(app=app)
        app_apis: Set[str] = {_strip_version(api) for entry in catalog_entries for api in entry.apis}
        api_microservice_map: Dict[str, str] = {
            _strip_version(api): entry.microservice
            for entry in catalog_entries
            for api in entry.apis
        }

        all_rules = self.alert_api_repository.get_all()
        adhoc_alerts = [
            r for r in all_rules
            if any(a in app_apis for a in r.apis_alertadas)
        ]
        channels = sorted({r.notification_channel for r in adhoc_alerts if r.notification_channel})

        default_alerts = [
            _to_default_api_view(d, app_apis)
            for d in self.default_alert_api_repository.get_all()
        ]

        return ApiSolutionView(
            app=app,
            default_alerts=default_alerts,
            adhoc_alerts=adhoc_alerts,
            api_microservice_map=api_microservice_map,
            channels=channels,
        )


def _to_default_api_view(default: DefaultAlertApi, app_apis: Set[str]) -> DefaultAlertApiView:
    excluded = set(default.excluded_apis) & app_apis
    is_disabled = bool(app_apis) and excluded == app_apis
    is_partial = bool(excluded) and not is_disabled
    return DefaultAlertApiView(
        raw_name=default.raw_name,
        name=default.display_name,
        description=default.display_description or default.raw_description,
        severity=default.severity,
        notification_channel=default.notification_channel,
        environments=["pro"],
        is_disabled=is_disabled,
        is_partial=is_partial,
        chips=sorted(excluded) if not is_disabled else [],
    )
