import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n
from fwkpy_lib_database.synchronous.middlewares import add_session_middleware

from alert_monitoring.api.application.services.alert_service import AlertService
from alert_monitoring.api.application.services.catalog_service import CatalogService
from alert_monitoring.api.application.services.catalog_app_api_service import CatalogAppApiService
from alert_monitoring.api.application.services.alert_api_service import AlertApiService
from alert_monitoring.api.driving.api_rest.adapters.sync_adapter import _run

from alert_monitoring.api.driven.postgres_repository.adapters.alert_repository import AlertRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.alert_api_repository import AlertApiRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_repository import CatalogAppRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_api_repository import CatalogAppApiRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_repository import DefaultAlertRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_api_repository import DefaultAlertApiRepositoryAdapter  # noqa
from fwkpy_lib_fastapi import FastAPIBuilder


class TestRunHelper:
    """Tests for the _run helper function in sync_adapter."""

    def test_run_returns_synced_count_on_success(self):
        result = _run(lambda: 42)
        assert result == {"synced": 42}

    def test_run_returns_error_on_exception(self):
        def failing():
            raise ValueError("Something went wrong")
        result = _run(failing)
        assert "error" in result
        assert "Something went wrong" in result["error"]

    def test_run_wraps_zero_result(self):
        result = _run(lambda: 0)
        assert result == {"synced": 0}


class TestSyncGlobalControllerAdapter:

    @classmethod
    def setup_class(cls):
        cls.app = FastAPIBuilder()
        add_session_middleware(cls.app)
        set_i18n()
        cls.client = TestClient(cls.app)
        translations_path = Path(os.path.dirname(__file__)).parent.parent.parent.parent.parent.parent
        load_translations(os.path.join(translations_path, 'alert_monitoring/api/boot/resources/i18n'))

    @patch.object(AlertApiService, AlertApiService.sync_alert_apis.__name__)
    @patch.object(AlertService, AlertService.sync_elastic_alerts.__name__)
    @patch.object(AlertService, AlertService.sync_prometheus_alerts.__name__)
    @patch.object(CatalogAppApiService, CatalogAppApiService.sync_catalog_app_api.__name__)
    @patch.object(CatalogService, CatalogService.sync_catalog.__name__)
    def test_sync_global_returns_200_on_success(
        self, mock_catalog, mock_catalog_api, mock_prometheus, mock_elastic, mock_alert_api
    ):
        """
        Given all services succeed
        When POST /sync/global
        Then should return 200 with results from all syncs
        """
        mock_catalog.return_value = 10
        mock_catalog_api.return_value = 5
        mock_prometheus.return_value = 20
        mock_elastic.return_value = 15
        mock_alert_api.return_value = 8

        response = self.client.post('/sync/global')

        assert response.status_code == 200
        data = response.json()
        assert 'duration_ms' in data
        assert 'catalog' in data

    @patch.object(CatalogService, CatalogService.sync_catalog.__name__)
    def test_sync_global_returns_500_when_catalog_fails(self, mock_catalog):
        """
        Given catalog service fails
        When POST /sync/global
        Then should return 500 with error info
        """
        mock_catalog.side_effect = RuntimeError("Catalog connection error")

        response = self.client.post('/sync/global')

        assert response.status_code == 500
        data = response.json()
        assert 'catalog' in data
        assert 'error' in data['catalog']

    @patch.object(CatalogAppApiService, CatalogAppApiService.sync_catalog_app_api.__name__)
    @patch.object(CatalogService, CatalogService.sync_catalog.__name__)
    def test_sync_global_returns_500_when_catalog_api_fails(self, mock_catalog, mock_catalog_api):
        """
        Given catalog succeeds but catalog_api service fails
        When POST /sync/global
        Then should return 500 and abort before running parallel syncs
        """
        mock_catalog.return_value = 10
        mock_catalog_api.side_effect = RuntimeError("Catalog API connection error")

        response = self.client.post('/sync/global')

        assert response.status_code == 500
        data = response.json()
        assert 'catalog_api' in data
        assert 'error' in data['catalog_api']

    @patch.object(AlertApiService, AlertApiService.sync_alert_apis.__name__)
    @patch.object(AlertService, AlertService.sync_elastic_alerts.__name__)
    @patch.object(AlertService, AlertService.sync_prometheus_alerts.__name__)
    @patch.object(CatalogAppApiService, CatalogAppApiService.sync_catalog_app_api.__name__)
    @patch.object(CatalogService, CatalogService.sync_catalog.__name__)
    def test_sync_global_includes_duration_ms(
        self, mock_catalog, mock_catalog_api, mock_prometheus, mock_elastic, mock_alert_api
    ):
        """
        Given all services succeed
        When POST /sync/global
        Then response should include duration_ms field
        """
        mock_catalog.return_value = 1
        mock_catalog_api.return_value = 1
        mock_prometheus.return_value = 1
        mock_elastic.return_value = 1
        mock_alert_api.return_value = 1

        response = self.client.post('/sync/global')

        assert response.status_code == 200
        assert isinstance(response.json().get('duration_ms'), int)
