import pytest

from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.services.catalog_service import CatalogService
from alert_monitoring.api.domain.models.catalog_app import CatalogApp


@pytest.fixture
def service(mocker):
    mocker.patch('alert_monitoring.api.application.services.catalog_service.AtlassianAssetsAdapter')
    return CatalogService(
        catalog_app_repository=mocker.MagicMock(spec=CatalogAppRepositoryPort),
        logger=mocker.MagicMock(),
    )


class TestCatalogServiceSyncCatalog:

    def test_fetches_from_atlassian_and_saves_all_apps(self, service):
        """
        Given Atlassian Assets returns a list of apps
        When sync_catalog is called
        Then it should save all apps and return how many were synced
        """
        apps = [CatalogApp(object_id='1', name='my-app'), CatalogApp(object_id='2', name='other-app')]
        service.atlassian_assets_adapter.fetch_catalog_apps.return_value = apps

        result = service.sync_catalog()

        assert result == 2
        service.catalog_app_repository.save_all.assert_called_once_with(apps)

    def test_returns_zero_when_no_apps_found(self, service):
        """
        Given Atlassian Assets returns no apps
        When sync_catalog is called
        Then it should save an empty list and return 0
        """
        service.atlassian_assets_adapter.fetch_catalog_apps.return_value = []

        result = service.sync_catalog()

        assert result == 0
        service.catalog_app_repository.save_all.assert_called_once_with([])


class TestCatalogServiceGetAllCatalogApps:

    def test_delegates_to_repository_without_filter(self, service):
        """
        Given no name filter
        When get_all_catalog_apps is called
        Then it should delegate to the repository with name=None
        """
        service.catalog_app_repository.get_all.return_value = [CatalogApp(object_id='1', name='my-app')]

        result = service.get_all_catalog_apps()

        assert len(result) == 1
        service.catalog_app_repository.get_all.assert_called_once_with(name=None)

    def test_passes_name_filter_to_repository(self, service):
        """
        Given a name filter
        When get_all_catalog_apps is called
        Then it should delegate to the repository with that filter
        """
        service.catalog_app_repository.get_all.return_value = []

        service.get_all_catalog_apps(name="my-app")

        service.catalog_app_repository.get_all.assert_called_once_with(name="my-app")
