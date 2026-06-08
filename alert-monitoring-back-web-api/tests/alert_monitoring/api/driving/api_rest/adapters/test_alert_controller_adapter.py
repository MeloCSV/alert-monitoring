import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n
from fwkpy_lib_database.synchronous.middlewares import add_session_middleware

from alert_monitoring.api.application.services.alert_service import AlertService
from alert_monitoring.api.driving.api_rest.mappers.alert_dto_mapper import AlertDTOMapper
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher
from alert_monitoring.api.domain.models.solution_view import SolutionView, DefaultAlertView
from alert_monitoring.api.domain.models.api_solution_view import ApiSolutionView, DefaultAlertApiView
from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.driving.api_rest.models.alert_response import AlertResponse

# Needed for the injection
from alert_monitoring.api.driven.postgres_repository.adapters.alert_repository import AlertRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.alert_api_repository import AlertApiRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_repository import CatalogAppRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_api_repository import CatalogAppApiRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_repository import DefaultAlertRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_api_repository import DefaultAlertApiRepositoryAdapter  # noqa
from fwkpy_lib_fastapi import FastAPIBuilder


def _make_alert(**kwargs):
    defaults = dict(
        name='test-alert',
        description='Test description',
        source_tool='Prometheus',
        severity='warning',
        environments=['pro'],
    )
    defaults.update(kwargs)
    return Alert(**defaults)


def _make_alert_response(**kwargs):
    defaults = dict(
        name='test-alert',
        description='Test description',
        source_tool='Prometheus',
        severity='warning',
        environments=['pro'],
    )
    defaults.update(kwargs)
    return AlertResponse(**defaults)


class TestAlertControllerAdapter:

    @classmethod
    def setup_class(cls):
        cls.app = FastAPIBuilder()
        add_session_middleware(cls.app)
        set_i18n()
        cls.client = TestClient(cls.app)
        translations_path = Path(os.path.dirname(__file__)).parent.parent.parent.parent.parent.parent
        load_translations(os.path.join(translations_path, 'alert_monitoring/api/boot/resources/i18n'))

    @patch.object(AlertService, AlertService.sync_prometheus_alerts.__name__)
    def test_should_sync_prometheus_alerts_and_return_201(self, mock_sync):
        """
        Given valid request
        When POST /alerts/sync
        Then should return 201 with count of saved rules
        """
        mock_sync.return_value = 42

        response = self.client.post('/alerts/sync')

        assert response.status_code == 201
        assert response.json()['saved'] == 42
        assert 'message' in response.json()

    @patch.object(AlertService, AlertService.sync_elastic_alerts.__name__)
    def test_should_sync_elastic_alerts_and_return_201(self, mock_sync):
        """
        Given valid request
        When POST /alerts/sync/elastic
        Then should return 201 with count of saved rules
        """
        mock_sync.return_value = 10

        response = self.client.post('/alerts/sync/elastic')

        assert response.status_code == 201
        assert response.json()['saved'] == 10

    @patch.object(AlertDTOMapper, AlertDTOMapper.to_models_decorator.__name__)
    @patch.object(AlertService, AlertService.get_all_alerts.__name__)
    def test_should_get_all_alerts_and_return_200(self, mock_get, mock_mapper):
        """
        Given valid request
        When GET /alerts
        Then should return list of alerts and status 200
        """
        mock_get.return_value = [_make_alert()]
        mock_mapper.return_value = [_make_alert_response()]

        response = self.client.get('/alerts')

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]['name'] == 'test-alert'

    @patch.object(AlertDTOMapper, AlertDTOMapper.to_models_decorator.__name__)
    @patch.object(AlertService, AlertService.get_all_alerts.__name__)
    def test_should_pass_query_params_as_filters_to_get_all_alerts(self, mock_get, mock_mapper):
        """
        Given query params with filters
        When GET /alerts
        Then should pass filters to the service and return the filtered results
        """
        mock_get.return_value = []
        mock_mapper.return_value = []

        response = self.client.get('/alerts?name=my-alert&severity=critical&solution=my-app')

        assert response.status_code == 200
        call_args = mock_get.call_args[0][0]  # first positional arg after self is AlertFilter
        assert call_args.name == 'my-alert'
        assert call_args.severity == 'critical'
        assert call_args.solution == 'my-app'

    @patch.object(AlertService, AlertService.get_default_alerts.__name__)
    def test_should_get_default_alerts_and_return_200(self, mock_get):
        """
        Given valid request
        When GET /alerts/defaults
        Then should return list of default alerts and status 200
        """
        mock_get.return_value = [
            DefaultAlert(
                raw_name='Default_Service_Status_KO',
                display_name='Estado del servicio KO',
                severity='warning',
                notification_channel='Microsoft Teams',
            )
        ]

        response = self.client.get('/alerts/defaults')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['raw_name'] == 'Default_Service_Status_KO'

    @patch.object(AlertService, AlertService.get_active_blackouts.__name__)
    def test_should_get_active_blackouts_and_return_200(self, mock_get):
        """
        Given valid request with solution filter
        When GET /alerts/blackouts?solution=my-app
        Then should return list of blackouts and status 200
        """
        mock_get.return_value = [
            Blackout(
                id='silence-abc123',
                matchers=[BlackoutMatcher(name='namespace', value='my-app', is_regex=False, is_equal=True)],
                starts_at='2025-01-01T00:00:00Z',
                ends_at='2025-12-31T23:59:59Z',
            )
        ]

        response = self.client.get('/alerts/blackouts?solution=my-app')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]['id'] == 'silence-abc123'
        assert data[0]['matchers'][0]['name'] == 'namespace'

    @patch.object(AlertService, AlertService.get_active_blackouts.__name__)
    def test_should_get_blackouts_without_solution_filter(self, mock_get):
        """
        Given request without solution
        When GET /alerts/blackouts
        Then should return all blackouts
        """
        mock_get.return_value = []

        response = self.client.get('/alerts/blackouts')

        assert response.status_code == 200
        assert response.json() == []

    @patch.object(AlertService, AlertService.get_solution_view.__name__)
    def test_should_get_solution_view_and_return_200(self, mock_get):
        """
        Given valid solution param
        When GET /alerts/view?solution=my-app
        Then should return solution view and status 200
        """
        mock_get.return_value = SolutionView(
            app='my-app',
            default_alerts=[
                DefaultAlertView(
                    raw_name='Default_Status',
                    name='Estado del servicio',
                    severity='warning',
                    is_disabled=False,
                    is_partial=True,
                    chips=['my-app-worker'],
                )
            ],
            adhoc_alerts=[_make_alert(solution='my-app')],
            channels=['Microsoft Teams'],
        )

        response = self.client.get('/alerts/view?solution=my-app')

        assert response.status_code == 200
        data = response.json()
        assert data['app'] == 'my-app'
        assert data['channels'] == ['Microsoft Teams']
        assert len(data['default_alerts']) == 1
        assert data['default_alerts'][0]['is_partial'] is True

    @patch.object(AlertService, AlertService.get_api_solution_view.__name__)
    def test_should_get_api_solution_view_and_return_200(self, mock_get):
        """
        Given valid app param
        When GET /alerts/api-view?app=my-app
        Then should return API solution view and status 200
        """
        mock_get.return_value = ApiSolutionView(
            app='my-app',
            default_alerts=[
                DefaultAlertApiView(
                    raw_name='Global_Rule',
                    name='Errores 500',
                    severity='critical',
                    is_disabled=False,
                    is_partial=False,
                )
            ],
            adhoc_alerts=[
                AlertApi(rule_id='rule-1', name='Errores 500 absence', apis_alertadas=['absence', 'employee'])
            ],
            api_microservice_map={'absence': 'absence-back', 'employee': 'employee-back'},
            channels=['ServiceNow'],
        )

        response = self.client.get('/alerts/api-view?app=my-app')

        assert response.status_code == 200
        data = response.json()
        assert data['app'] == 'my-app'
        assert data['channels'] == ['ServiceNow']
        assert 'absence' in data['api_microservice_map']
        assert len(data['adhoc_alerts']) == 1
