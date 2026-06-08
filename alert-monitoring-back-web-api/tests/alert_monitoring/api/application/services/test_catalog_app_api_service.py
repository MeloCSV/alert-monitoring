from unittest.mock import MagicMock, patch

import pytest

from alert_monitoring.api.application.ports.driven.catalog_app_api_repository_port import CatalogAppApiRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.services.catalog_app_api_service import CatalogAppApiService
from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi


@pytest.fixture
def service(mocker):
    mocker.patch(
        'alert_monitoring.api.application.services.catalog_app_api_service.CatalogAppApiFileAdapter'
    )
    return CatalogAppApiService(
        catalog_app_api_repository=mocker.MagicMock(spec=CatalogAppApiRepositoryPort),
        catalog_app_repository=mocker.MagicMock(spec=CatalogAppRepositoryPort),
        logger=mocker.MagicMock(),
    )


class TestCatalogAppApiServiceProcessEntries:

    def test_groups_entries_by_microservice(self, service):
        service.catalog_app_repository.get_all.return_value = [
            CatalogApp(object_id='1', name='my-app')
        ]
        entries = [
            {"child": "my-back", "parent": "api-a"},
            {"child": "my-back", "parent": "api-b"},
        ]
        catalog_lookup = {"my": "my-app"}

        result = service._process_entries(entries, catalog_lookup)

        assert len(result) == 1
        assert result[0].microservice == "my-back"
        assert set(result[0].apis) == {"api-a", "api-b"}

    def test_ignores_entries_with_empty_child_or_parent(self, service):
        entries = [
            {"child": "", "parent": "api-a"},
            {"child": "my-back", "parent": ""},
            {"child": "my-back", "parent": "api-valid"},
        ]
        catalog_lookup = {"my": "my-app"}

        result = service._process_entries(entries, catalog_lookup)

        assert len(result) == 1
        assert result[0].apis == ["api-valid"]

    def test_ignores_microservices_not_in_catalog(self, service):
        entries = [{"child": "unknown-back", "parent": "api-a"}]
        catalog_lookup = {"my": "my-app"}

        result = service._process_entries(entries, catalog_lookup)

        assert result == []

    def test_deduplicates_apis(self, service):
        entries = [
            {"child": "my-back", "parent": "api-a"},
            {"child": "my-back", "parent": "api-a"},
        ]
        catalog_lookup = {"my": "my-app"}

        result = service._process_entries(entries, catalog_lookup)

        assert result[0].apis.count("api-a") == 1

    def test_apis_are_sorted(self, service):
        entries = [
            {"child": "my-back", "parent": "z-api"},
            {"child": "my-back", "parent": "a-api"},
        ]
        catalog_lookup = {"my": "my-app"}

        result = service._process_entries(entries, catalog_lookup)

        assert result[0].apis == ["a-api", "z-api"]


class TestCatalogAppApiServiceResolveApp:

    def test_resolves_app_by_prefix(self):
        lookup = {"my": "My-App", "other": "Other-App"}
        result = CatalogAppApiService._resolve_app("my-back", lookup)
        assert result == "My-App"

    def test_returns_none_when_prefix_not_in_catalog(self):
        lookup = {"other": "Other-App"}
        result = CatalogAppApiService._resolve_app("my-back", lookup)
        assert result is None

    def test_uses_first_segment_before_dash(self):
        lookup = {"abc": "Abc-App"}
        result = CatalogAppApiService._resolve_app("abc-def-ghi", lookup)
        assert result == "Abc-App"

    def test_case_insensitive_lookup(self):
        lookup = {"my": "My-App"}
        result = CatalogAppApiService._resolve_app("MY-back", lookup)
        assert result == "My-App"


class TestCatalogAppApiServiceGetAll:

    def test_get_all_delegates_to_repository(self, service):
        service.repository.get_all.return_value = [
            CatalogAppApi(app="my-app", microservice="my-back", apis=["api-a"])
        ]

        result = service.get_all()

        assert len(result) == 1
        service.repository.get_all.assert_called_once_with(app=None)

    def test_get_all_passes_app_filter(self, service):
        service.repository.get_all.return_value = []

        service.get_all(app="my-app")

        service.repository.get_all.assert_called_once_with(app="my-app")
