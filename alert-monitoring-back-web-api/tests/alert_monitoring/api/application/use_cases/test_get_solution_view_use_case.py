from typing import List
from unittest.mock import MagicMock

import pytest

from alert_monitoring.api.application.use_cases.get_solution_view_use_case import (
    GetSolutionViewUseCase,
    _evaluate,
    _regex_matches,
    _is_prefix_of,
    _literal_prefix,
)
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.solution_view import SolutionView


def _make_alert(**kwargs) -> Alert:
    defaults = dict(
        name='adhoc-alert',
        description='desc',
        source_tool='Prometheus',
        severity='warning',
        environments=['pro'],
        solution='my-app',
        microservice='my-app-back',
    )
    defaults.update(kwargs)
    return Alert(**defaults)


def _make_default_alert(**kwargs) -> DefaultAlert:
    defaults = dict(
        raw_name='Default_Status',
        display_name='Estado del servicio',
        severity='warning',
        excluded_namespaces=[],
        included_namespaces=[],
        excluded_jobs=[],
    )
    defaults.update(kwargs)
    return DefaultAlert(**defaults)


class TestGetSolutionViewUseCase:

    @pytest.fixture
    def alert_repo(self):
        return MagicMock(spec=AlertRepositoryPort)

    @pytest.fixture
    def default_alert_repo(self):
        return MagicMock(spec=DefaultAlertRepositoryPort)

    @pytest.fixture
    def use_case(self, alert_repo, default_alert_repo):
        return GetSolutionViewUseCase(
            alert_repository=alert_repo,
            default_alert_repository=default_alert_repo,
        )

    def test_should_return_solution_view_with_app_name(self, use_case, alert_repo, default_alert_repo):
        """
        Given a solution name
        When execute
        Then should return SolutionView with correct app field
        """
        alert_repo.get_all.return_value = []
        default_alert_repo.get_all.return_value = []

        result = use_case.execute('my-app')

        assert isinstance(result, SolutionView)
        assert result.app == 'my-app'

    def test_should_include_adhoc_alerts_for_solution(self, use_case, alert_repo, default_alert_repo):
        """
        Given alerts exist for solution
        When execute
        Then should include them in adhoc_alerts
        """
        alerts = [_make_alert(), _make_alert(name='second-alert')]
        alert_repo.get_all.return_value = alerts
        default_alert_repo.get_all.return_value = []

        result = use_case.execute('my-app')

        assert result.adhoc_alerts == alerts
        alert_repo.get_all.assert_called_once()
        called_filter: AlertFilter = alert_repo.get_all.call_args[0][0]
        assert called_filter.solution == 'my-app'

    def test_should_collect_unique_channels_from_alerts(self, use_case, alert_repo, default_alert_repo):
        """
        Given alerts with different channels
        When execute
        Then should collect unique channels sorted
        """
        alert_repo.get_all.return_value = [
            _make_alert(notification_channel='Microsoft Teams'),
            _make_alert(notification_channel='ServiceNow'),
            _make_alert(notification_channel='Microsoft Teams'),
        ]
        default_alert_repo.get_all.return_value = []

        result = use_case.execute('my-app')

        assert result.channels == ['Microsoft Teams', 'ServiceNow']

    def test_should_include_default_alerts_as_not_disabled_when_no_exclusions(
        self, use_case, alert_repo, default_alert_repo
    ):
        """
        Given default alert with no exclusions
        When execute for any solution
        Then is_disabled and is_partial should both be False
        """
        alert_repo.get_all.return_value = []
        default_alert_repo.get_all.return_value = [
            _make_default_alert(excluded_namespaces=[], excluded_jobs=[])
        ]

        result = use_case.execute('my-app')

        assert len(result.default_alerts) == 1
        assert result.default_alerts[0].is_disabled is False
        assert result.default_alerts[0].is_partial is False
        assert result.default_alerts[0].chips == []

    def test_should_mark_default_alert_as_disabled_when_solution_fully_excluded(
        self, use_case, alert_repo, default_alert_repo
    ):
        """
        Given default alert that excludes the solution namespace by exact regex
        When execute for that solution
        Then is_disabled should be True
        """
        alert_repo.get_all.return_value = []
        default_alert_repo.get_all.return_value = [
            _make_default_alert(excluded_namespaces=['my-app'])
        ]

        result = use_case.execute('my-app')

        view = result.default_alerts[0]
        assert view.is_disabled is True
        assert view.is_partial is False
        assert view.chips == []

    def test_should_mark_default_alert_as_partial_when_microservice_excluded(
        self, use_case, alert_repo, default_alert_repo
    ):
        """
        Given default alert that excludes a microservice prefix
        When execute for solution with matching microservices
        Then is_partial should be True with the microservice in chips
        """
        alert_repo.get_all.return_value = [_make_alert(microservice='my-app-back')]
        default_alert_repo.get_all.return_value = [
            _make_default_alert(excluded_namespaces=['my-app-back-.*'])
        ]

        result = use_case.execute('my-app')

        view = result.default_alerts[0]
        assert view.is_disabled is False
        assert view.is_partial is True
        assert len(view.chips) > 0

    def test_should_re_enable_alert_when_namespace_is_in_included(
        self, use_case, alert_repo, default_alert_repo
    ):
        """
        Given excluded namespace that is also re-included
        When execute
        Then is_disabled should be False (re-inclusion wins)
        """
        alert_repo.get_all.return_value = []
        default_alert_repo.get_all.return_value = [
            _make_default_alert(
                excluded_namespaces=['my-app'],
                included_namespaces=['my-app'],
            )
        ]

        result = use_case.execute('my-app')

        view = result.default_alerts[0]
        assert view.is_disabled is False

    def test_should_use_display_description_when_available(
        self, use_case, alert_repo, default_alert_repo
    ):
        """
        Given default alert with both raw and display description
        When execute
        Then view description should use display_description
        """
        alert_repo.get_all.return_value = []
        default_alert_repo.get_all.return_value = [
            _make_default_alert(
                raw_description='Raw technical message',
                display_description='Descripción amigable para la UI',
            )
        ]

        result = use_case.execute('my-app')

        assert result.default_alerts[0].description == 'Descripción amigable para la UI'

    def test_should_fall_back_to_raw_description_when_no_display_description(
        self, use_case, alert_repo, default_alert_repo
    ):
        """
        Given default alert with only raw description
        When execute
        Then view description should use raw_description
        """
        alert_repo.get_all.return_value = []
        default_alert_repo.get_all.return_value = [
            _make_default_alert(raw_description='Raw technical message', display_description=None)
        ]

        result = use_case.execute('my-app')

        assert result.default_alerts[0].description == 'Raw technical message'


class TestGetSolutionViewEdgeCases:
    """Tests covering edge cases in the pure helper functions."""

    def test_excluded_jobs_causes_partial(self):
        default = _make_default_alert(excluded_jobs=['my-app-worker'])
        is_disabled, is_partial, chips = _evaluate(default, 'my-app', set())
        assert is_partial is True
        assert 'my-app-worker' in chips

    def test_excluded_jobs_not_triggered_when_no_prefix_match(self):
        default = _make_default_alert(excluded_jobs=['other-worker'])
        is_disabled, is_partial, chips = _evaluate(default, 'my-app', set())
        assert is_partial is False

    def test_regex_matches_returns_false_for_invalid_regex(self):
        assert _regex_matches('my-app', '[invalid**') is False

    def test_is_prefix_of_returns_false_for_empty_target(self):
        assert _is_prefix_of('', 'my-app-back') is False

    def test_literal_prefix_handles_backslash_escape(self):
        result = _literal_prefix('my\\-app-back')
        assert result == 'my-app-back'

    def test_literal_prefix_stops_at_regex_special_char(self):
        result = _literal_prefix('my-app.*')
        assert result == 'my-app'
