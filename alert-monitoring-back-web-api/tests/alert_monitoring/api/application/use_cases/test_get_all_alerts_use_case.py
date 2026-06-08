from typing import List
from unittest.mock import MagicMock

import pytest

from alert_monitoring.api.application.use_cases.get_all_alerts_use_case import GetAllAlertsUseCase
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter


def _make_alert(**kwargs) -> Alert:
    defaults = dict(
        name='test-alert',
        description='Test description',
        source_tool='Prometheus',
        severity='warning',
        environments=['pro'],
    )
    defaults.update(kwargs)
    return Alert(**defaults)


class TestGetAllAlertsUseCase:

    @pytest.fixture
    def repository_mock(self):
        return MagicMock(spec=AlertRepositoryPort)

    @pytest.fixture
    def use_case(self, repository_mock):
        return GetAllAlertsUseCase(repository=repository_mock)

    def test_should_return_alerts_from_repository(self, use_case, repository_mock):
        """
        Given repository with alerts
        When execute without filters
        Then should return all alerts from repository
        """
        expected = [_make_alert(name='alert-1'), _make_alert(name='alert-2')]
        repository_mock.get_all.return_value = expected

        result = use_case.execute()

        assert result == expected
        repository_mock.get_all.assert_called_once_with(None)

    def test_should_pass_filters_to_repository(self, use_case, repository_mock):
        """
        Given filters provided
        When execute with filters
        Then should delegate filters to repository
        """
        filters = AlertFilter(name='my-alert', severity='critical', solution='my-app')
        repository_mock.get_all.return_value = []

        use_case.execute(filters)

        repository_mock.get_all.assert_called_once_with(filters)

    def test_should_return_empty_list_when_no_alerts(self, use_case, repository_mock):
        """
        Given empty repository
        When execute
        Then should return empty list
        """
        repository_mock.get_all.return_value = []

        result = use_case.execute()

        assert result == []
        assert isinstance(result, List)

    def test_should_return_list_of_alert_instances(self, use_case, repository_mock):
        """
        Given repository returns alerts
        When execute
        Then should return list of Alert instances
        """
        repository_mock.get_all.return_value = [
            _make_alert(source_tool='Prometheus'),
            _make_alert(source_tool='Elastic'),
        ]

        result = use_case.execute()

        assert all(isinstance(a, Alert) for a in result)
