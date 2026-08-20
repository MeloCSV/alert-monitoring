import pytest

from alert_monitoring.api.application.services.alert_api_service import AlertApiService
from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi


@pytest.fixture
def service(mocker):
    mocker.patch('alert_monitoring.api.application.services.alert_api_service.KibanaAdapter')
    mocker.patch('alert_monitoring.api.application.services.alert_api_service.KibanaRuleMapper')
    return AlertApiService(
        alert_api_repository=mocker.MagicMock(),
        default_alert_api_repository=mocker.MagicMock(),
        logger=mocker.MagicMock(),
    )


class TestAlertApiServiceSyncAlertApis:

    def test_syncs_default_and_adhoc_rules_from_all_kibana_configs(self, service):
        """
        Given Kibana returns rules for two configs, each split into default and adhoc rules
        When sync_alert_apis is called
        Then it should upsert the default rules, prune stale ones, and replace the adhoc rules
        """
        config_a, config_b = object(), object()
        service.kibana_adapter.fetch_rules_by_config.return_value = [
            (config_a, [{"name": "[global] rule a"}]),
            (config_b, [{"name": "rule b"}]),
        ]
        default_a = DefaultAlertApi(raw_name="rule-a", display_name="Rule A")
        adhoc_b = AlertApi(rule_id="1", name="rule b")
        service.kibana_rule_mapper.to_domain_split.side_effect = [
            ([default_a], []),
            ([], [adhoc_b]),
        ]

        result = service.sync_alert_apis()

        assert result == 2
        service.default_alert_api_repository.upsert_batch.assert_called_once_with([default_a])
        service.default_alert_api_repository.delete_where_not_in.assert_called_once_with(["rule-a"])
        service.alert_api_repository.delete_all.assert_called_once()
        service.alert_api_repository.save_all.assert_called_once_with([adhoc_b])

    def test_returns_zero_when_no_rules_found(self, service):
        """
        Given Kibana returns no rules at all
        When sync_alert_apis is called
        Then it should still prune and replace with empty batches and return 0
        """
        service.kibana_adapter.fetch_rules_by_config.return_value = []

        result = service.sync_alert_apis()

        assert result == 0
        service.default_alert_api_repository.upsert_batch.assert_called_once_with([])
        service.default_alert_api_repository.delete_where_not_in.assert_called_once_with([])
        service.alert_api_repository.save_all.assert_called_once_with([])


class TestAlertApiServiceGetAlertApis:

    def test_delegates_to_repository_without_filter(self, service):
        """
        Given no api filter
        When get_alert_apis is called
        Then it should delegate to the repository with api=None
        """
        service.alert_api_repository.get_all.return_value = [AlertApi(rule_id="1", name="rule a")]

        result = service.get_alert_apis()

        assert len(result) == 1
        service.alert_api_repository.get_all.assert_called_once_with(api=None)

    def test_passes_api_filter_to_repository(self, service):
        """
        Given an api filter
        When get_alert_apis is called
        Then it should delegate to the repository with that filter
        """
        service.alert_api_repository.get_all.return_value = []

        service.get_alert_apis(api="payroll")

        service.alert_api_repository.get_all.assert_called_once_with(api="payroll")


class TestAlertApiServiceGetApis:

    def test_delegates_to_repository_for_distinct_apis(self, service):
        """
        Given the repository knows about distinct APIs
        When get_apis is called
        Then it should return the repository's distinct API names
        """
        service.alert_api_repository.get_distinct_apis.return_value = ["absence", "payroll"]

        result = service.get_apis()

        assert result == ["absence", "payroll"]
        service.alert_api_repository.get_distinct_apis.assert_called_once()
