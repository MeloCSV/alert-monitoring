import pytest
from unittest.mock import MagicMock

from alert_monitoring.api.application.use_cases.get_api_solution_view_use_case import (
    GetApiSolutionViewUseCase,
    _strip_version,
    _to_default_api_view,
)
from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi
from alert_monitoring.api.domain.models.alert_api import AlertApi


# ---------------------------------------------------------------------------
# _strip_version helper
# ---------------------------------------------------------------------------

class TestStripVersion:
    def test_strips_version_suffix(self):
        assert _strip_version("my-api v2") == "my-api"

    def test_strips_version_suffix_v10(self):
        assert _strip_version("some-api v10") == "some-api"

    def test_no_version_unchanged(self):
        assert _strip_version("my-api") == "my-api"

    def test_version_in_middle_not_stripped(self):
        result = _strip_version("v2-api")
        assert result == "v2-api"


# ---------------------------------------------------------------------------
# _to_default_api_view helper
# ---------------------------------------------------------------------------

def _make_default_api(raw_name='Global_Rule', display_name='Rule', excluded_apis=None, **kwargs):
    return DefaultAlertApi(
        raw_name=raw_name,
        display_name=display_name,
        raw_description='raw desc',
        display_description=None,
        severity='warning',
        notification_channel='Microsoft Teams',
        excluded_apis=excluded_apis or [],
    )


class TestToDefaultApiView:
    def test_not_disabled_when_no_app_apis(self):
        default = _make_default_api(excluded_apis=['api-a'])
        view = _to_default_api_view(default, app_apis=set())
        assert view.is_disabled is False

    def test_disabled_when_all_app_apis_excluded(self):
        default = _make_default_api(excluded_apis=['api-a', 'api-b'])
        view = _to_default_api_view(default, app_apis={'api-a', 'api-b'})
        assert view.is_disabled is True
        assert view.is_partial is False

    def test_partial_when_some_apis_excluded(self):
        default = _make_default_api(excluded_apis=['api-a'])
        view = _to_default_api_view(default, app_apis={'api-a', 'api-b'})
        assert view.is_partial is True
        assert view.is_disabled is False

    def test_chips_contain_excluded_apis_when_partial(self):
        default = _make_default_api(excluded_apis=['api-a'])
        view = _to_default_api_view(default, app_apis={'api-a', 'api-b'})
        assert 'api-a' in view.chips

    def test_chips_empty_when_disabled(self):
        default = _make_default_api(excluded_apis=['api-a'])
        view = _to_default_api_view(default, app_apis={'api-a'})
        assert view.chips == []

    def test_uses_display_description_when_available(self):
        default = DefaultAlertApi(
            raw_name='R', display_name='N', raw_description='raw',
            display_description='display desc', severity='warning',
            notification_channel=None, excluded_apis=[],
        )
        view = _to_default_api_view(default, app_apis=set())
        assert view.description == 'display desc'

    def test_falls_back_to_raw_description_when_no_display(self):
        default = _make_default_api()
        view = _to_default_api_view(default, app_apis=set())
        assert view.description == 'raw desc'


# ---------------------------------------------------------------------------
# GetApiSolutionViewUseCase.execute
# ---------------------------------------------------------------------------

@pytest.fixture
def repos():
    catalog_repo = MagicMock()
    default_repo = MagicMock()
    alert_repo = MagicMock()
    return catalog_repo, default_repo, alert_repo


@pytest.fixture
def use_case(repos):
    catalog_repo, default_repo, alert_repo = repos
    return GetApiSolutionViewUseCase(
        catalog_app_api_repository=catalog_repo,
        default_alert_api_repository=default_repo,
        alert_api_repository=alert_repo,
    )


class TestGetApiSolutionViewUseCaseExecute:
    def test_returns_api_solution_view_with_app(self, use_case, repos):
        catalog_repo, default_repo, alert_repo = repos
        catalog_repo.get_all.return_value = []
        default_repo.get_all.return_value = []
        alert_repo.get_all.return_value = []

        result = use_case.execute('my-app')

        assert result.app == 'my-app'

    def test_filters_adhoc_alerts_by_app_apis(self, use_case, repos):
        catalog_repo, default_repo, alert_repo = repos

        entry = MagicMock()
        entry.apis = ['absence v1', 'employee']
        entry.microservice = 'absence-back'
        catalog_repo.get_all.return_value = [entry]

        matching = MagicMock(spec=AlertApi)
        matching.apis_alertadas = ['absence']
        matching.notification_channel = 'ServiceNow'

        unrelated = MagicMock(spec=AlertApi)
        unrelated.apis_alertadas = ['payroll']
        unrelated.notification_channel = None

        alert_repo.get_all.return_value = [matching, unrelated]
        default_repo.get_all.return_value = []

        result = use_case.execute('my-app')

        assert len(result.adhoc_alerts) == 1
        assert result.adhoc_alerts[0] is matching

    def test_strips_version_from_catalog_apis(self, use_case, repos):
        catalog_repo, default_repo, alert_repo = repos

        entry = MagicMock()
        entry.apis = ['my-api v3']
        entry.microservice = 'my-back'
        catalog_repo.get_all.return_value = [entry]

        rule = MagicMock(spec=AlertApi)
        rule.apis_alertadas = ['my-api']
        rule.notification_channel = None
        alert_repo.get_all.return_value = [rule]
        default_repo.get_all.return_value = []

        result = use_case.execute('my-app')

        assert len(result.adhoc_alerts) == 1

    def test_channels_sorted_and_deduplicated(self, use_case, repos):
        catalog_repo, default_repo, alert_repo = repos

        entry = MagicMock()
        entry.apis = ['api-a']
        entry.microservice = 'svc'
        catalog_repo.get_all.return_value = [entry]

        r1 = MagicMock(spec=AlertApi)
        r1.apis_alertadas = ['api-a']
        r1.notification_channel = 'ServiceNow'

        r2 = MagicMock(spec=AlertApi)
        r2.apis_alertadas = ['api-a']
        r2.notification_channel = 'Microsoft Teams'

        alert_repo.get_all.return_value = [r1, r2]
        default_repo.get_all.return_value = []

        result = use_case.execute('my-app')

        assert result.channels == sorted({'ServiceNow', 'Microsoft Teams'})

    def test_api_microservice_map_built_correctly(self, use_case, repos):
        catalog_repo, default_repo, alert_repo = repos

        entry = MagicMock()
        entry.apis = ['absence v1']
        entry.microservice = 'absence-back'
        catalog_repo.get_all.return_value = [entry]

        alert_repo.get_all.return_value = []
        default_repo.get_all.return_value = []

        result = use_case.execute('my-app')

        assert result.api_microservice_map.get('absence') == 'absence-back'
