import pytest
from unittest.mock import MagicMock, patch

from alert_monitoring.api.application.services.alert_service import AlertService
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_api_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_api_repository_port import CatalogAppApiRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_api_repository_port import DefaultAlertApiRepositoryPort
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.api_solution_view import ApiSolutionView
from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher
from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.solution_view import SolutionView
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule


def _make_blackout(matchers: list[BlackoutMatcher]) -> Blackout:
    return Blackout(id='test-id', matchers=matchers)


def _matcher(name: str, value: str, is_regex: bool = False, is_equal: bool = True) -> BlackoutMatcher:
    return BlackoutMatcher(name=name, value=value, is_regex=is_regex, is_equal=is_equal)


def _make_alert(**kwargs) -> Alert:
    defaults = dict(name='test', description='desc', source_tool='Prometheus',
                    severity='warning', environments=['pro'])
    defaults.update(kwargs)
    return Alert(**defaults)


@pytest.fixture
def service(mocker):
    mocker.patch('alert_monitoring.api.application.services.alert_service.PrometheusAdapter')
    mocker.patch('alert_monitoring.api.application.services.alert_service.KibanaAdapter')
    mocker.patch('alert_monitoring.api.application.services.alert_service.ElasticAdapter')
    mocker.patch('alert_monitoring.api.application.services.alert_service.AlertManagerAdapter')

    return AlertService(
        alert_repository=mocker.MagicMock(spec=AlertRepositoryPort),
        alert_api_repository=mocker.MagicMock(spec=AlertApiRepositoryPort),
        catalog_app_repository=mocker.MagicMock(spec=CatalogAppRepositoryPort),
        catalog_app_api_repository=mocker.MagicMock(spec=CatalogAppApiRepositoryPort),
        default_alert_repository=mocker.MagicMock(spec=DefaultAlertRepositoryPort),
        default_alert_api_repository=mocker.MagicMock(spec=DefaultAlertApiRepositoryPort),
        logger=mocker.MagicMock(),
    )


class TestBlackoutMatchesSolution:
    """Unit tests for _blackout_matches_solution (pure logic)."""

    @pytest.fixture
    def match(self):
        instance = MagicMock()
        instance._APP_MATCHER_FIELDS = AlertService._APP_MATCHER_FIELDS
        return lambda blackout, solution: AlertService._blackout_matches_solution(instance, blackout, solution)

    def test_exact_namespace_match(self, match):
        b = _make_blackout([_matcher('namespace', 'my-app')])
        assert match(b, 'my-app') is True

    def test_back_variant_matches(self, match):
        b = _make_blackout([_matcher('namespace', 'my-app-back')])
        assert match(b, 'my-app') is True

    def test_front_variant_matches(self, match):
        b = _make_blackout([_matcher('namespace', 'my-app-front')])
        assert match(b, 'my-app') is True

    def test_unrelated_namespace_does_not_match(self, match):
        b = _make_blackout([_matcher('namespace', 'other-app')])
        assert match(b, 'my-app') is False

    def test_regex_matcher_matches_solution(self, match):
        b = _make_blackout([_matcher('namespace', 'my-app.*', is_regex=True)])
        assert match(b, 'my-app') is True

    def test_regex_matcher_matches_back_variant(self, match):
        b = _make_blackout([_matcher('namespace', 'my-app-.*', is_regex=True)])
        assert match(b, 'my-app') is True

    def test_non_matching_field_name_is_ignored(self, match):
        b = _make_blackout([_matcher('alertname', 'my-app')])
        assert match(b, 'my-app') is False

    def test_is_equal_false_is_ignored(self, match):
        b = _make_blackout([_matcher('namespace', 'my-app', is_equal=False)])
        assert match(b, 'my-app') is False

    def test_deployment_field_matches(self, match):
        b = _make_blackout([_matcher('deployment', 'my-app-back')])
        assert match(b, 'my-app') is True

    def test_solucion_field_matches(self, match):
        b = _make_blackout([_matcher('solucion', 'my-app')])
        assert match(b, 'my-app') is True

    def test_case_insensitive_match(self, match):
        b = _make_blackout([_matcher('namespace', 'MY-APP')])
        assert match(b, 'my-app') is True

    def test_prefix_child_namespace_matches(self, match):
        b = _make_blackout([_matcher('namespace', 'my-app-worker')])
        assert match(b, 'my-app') is True


class TestAlertServiceDelegatingMethods:
    """Tests for AlertService methods that delegate to use cases."""

    def test_get_all_alerts_delegates_to_use_case(self, service, mocker):
        """
        Given alerts in the use case
        When get_all_alerts is called
        Then should return results from the use case
        """
        expected = [_make_alert()]
        mocker.patch.object(service.get_all_use_case, 'execute', return_value=expected)

        result = service.get_all_alerts()

        assert result == expected
        service.get_all_use_case.execute.assert_called_once_with(None)

    def test_get_all_alerts_passes_filters(self, service, mocker):
        """
        Given filters
        When get_all_alerts is called
        Then should pass filters to use case
        """
        filters = AlertFilter(solution='my-app')
        mocker.patch.object(service.get_all_use_case, 'execute', return_value=[])

        service.get_all_alerts(filters)

        service.get_all_use_case.execute.assert_called_once_with(filters)

    def test_get_default_alerts_returns_from_repository(self, service):
        """
        Given default alerts in repository
        When get_default_alerts is called
        Then should return them
        """
        expected = [DefaultAlert(raw_name='Default_Status', display_name='Estado', severity='warning')]
        service.default_alert_repository.get_all.return_value = expected

        result = service.get_default_alerts()

        assert result == expected

    def test_get_solution_view_delegates_to_use_case(self, service, mocker):
        """
        Given a solution
        When get_solution_view is called
        Then should delegate to use case and return result
        """
        expected = SolutionView(app='my-app')
        mocker.patch.object(service.get_solution_view_use_case, 'execute', return_value=expected)

        result = service.get_solution_view('my-app')

        assert result == expected
        service.get_solution_view_use_case.execute.assert_called_once_with('my-app')

    def test_get_active_blackouts_filters_by_solution(self, service):
        """
        Given blackouts where some match the solution
        When get_active_blackouts is called with a solution
        Then should return only matching blackouts
        """
        matching = Blackout(id='1', matchers=[BlackoutMatcher(name='namespace', value='my-app', is_regex=False, is_equal=True)])
        non_matching = Blackout(id='2', matchers=[BlackoutMatcher(name='namespace', value='other-app', is_regex=False, is_equal=True)])
        service.alertmanager_adapter.fetch_active_blackouts.return_value = [matching, non_matching]

        result = service.get_active_blackouts('my-app')

        assert len(result) == 1
        assert result[0].id == '1'

    def test_get_active_blackouts_without_solution_returns_all(self, service):
        """
        Given blackouts
        When get_active_blackouts is called without solution
        Then should return all blackouts
        """
        blackouts = [
            Blackout(id='1', matchers=[]),
            Blackout(id='2', matchers=[]),
        ]
        service.alertmanager_adapter.fetch_active_blackouts.return_value = blackouts

        result = service.get_active_blackouts()

        assert len(result) == 2

    def test_get_api_solution_view_delegates_to_use_case(self, service, mocker):
        expected = ApiSolutionView(app='my-app', default_alerts=[], adhoc_alerts=[], api_microservice_map={}, channels=[])
        mocker.patch.object(service.get_api_solution_view_use_case, 'execute', return_value=expected)

        result = service.get_api_solution_view('my-app')

        assert result == expected
        service.get_api_solution_view_use_case.execute.assert_called_once_with('my-app')

    def test_invalid_regex_in_blackout_matcher_is_skipped(self, service):
        invalid = Blackout(id='1', matchers=[
            BlackoutMatcher(name='namespace', value='[invalid**', is_regex=True, is_equal=True)
        ])
        result = service._blackout_matches_solution(invalid, 'my-app')
        assert result is False

    def test_build_catalog_lookup_returns_lowercased_keys(self, service):
        service.catalog_app_repository.get_all.return_value = [
            CatalogApp(object_id='1', name='My-App'),
            CatalogApp(object_id='2', name='Other-App'),
        ]
        result = service._build_catalog_lookup()
        assert result['my-app'] == 'My-App'
        assert result['other-app'] == 'Other-App'

    def test_normalize_solutions_maps_to_canonical_name(self, service):
        catalog = {'my-app': 'My-App'}
        alert = _make_alert(solution='my-app')
        service._normalize_solutions([alert], catalog)
        assert alert.solution == 'My-App'

    def test_normalize_solutions_warns_when_unknown(self, service):
        catalog = {}
        alert = _make_alert(solution='unknown-app')
        service._normalize_solutions([alert], catalog)
        service.logger.warning.assert_called_once()

    def test_normalize_solutions_skips_alerts_without_solution(self, service):
        catalog = {}
        alert = _make_alert(solution=None)
        service._normalize_solutions([alert], catalog)
        service.logger.warning.assert_not_called()

    def test_sync_prometheus_alerts_deletes_and_saves(self, service):
        rules = [
            PrometheusRule(alert='MyAlert', expr='', labels={'severity': 'warning'}, annotations={}, group_name='my-app.rules'),
        ]
        service.prometheus_adapter.fetch_rules.return_value = rules
        service.catalog_app_repository.get_all.return_value = []
        service.default_alert_repository.upsert_batch = MagicMock()

        count = service.sync_prometheus_alerts()

        assert count == 1
        service.alert_repository.delete_by_source_tool.assert_called_once_with('Prometheus')

    def test_sync_elastic_alerts_deletes_and_saves(self, service, mocker):
        service.kibana_adapter.fetch_rules.return_value = []
        service.elastic_adapter.parse_rules.return_value = []
        mocker.patch.object(service.elastic_mapper, 'to_domain', return_value=[])
        service.catalog_app_repository.get_all.return_value = []

        count = service.sync_elastic_alerts()

        assert count == 0
        service.alert_repository.delete_by_source_tool.assert_called_once_with('Elastic')

    def test_upsert_default_alerts_is_noop_for_empty_list(self, service):
        service._upsert_default_alerts([])
        service.default_alert_repository.upsert_batch.assert_not_called()

    def test_upsert_default_alerts_calls_repository(self, service):
        rule = PrometheusRule(
            alert='Default_Status some label',
            expr='namespace!~"excl-ns"',
            labels={'severity': 'warning'},
            annotations={'message': 'Service down'},
            group_name='default.rules',
        )
        service._upsert_default_alerts([rule])
        service.default_alert_repository.upsert_batch.assert_called_once()
