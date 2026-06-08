import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n
from fwkpy_lib_database.synchronous.middlewares import add_session_middleware

from alert_monitoring.api.application.services.catalog_service import CatalogService
from alert_monitoring.api.application.services.alert_api_service import AlertApiService
from alert_monitoring.api.application.services.catalog_app_api_service import CatalogAppApiService
from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi
from alert_monitoring.api.domain.models.alert_api import AlertApi

from alert_monitoring.api.driven.postgres_repository.adapters.alert_repository import AlertRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.alert_api_repository import AlertApiRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_repository import CatalogAppRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_api_repository import CatalogAppApiRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_repository import DefaultAlertRepositoryAdapter  # noqa
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_api_repository import DefaultAlertApiRepositoryAdapter  # noqa
from fwkpy_lib_fastapi import FastAPIBuilder


class TestCatalogControllerAdapter:

    @classmethod
    def setup_class(cls):
        cls.app = FastAPIBuilder()
        add_session_middleware(cls.app)
        set_i18n()
        cls.client = TestClient(cls.app)
        translations_path = Path(os.path.dirname(__file__)).parent.parent.parent.parent.parent.parent
        load_translations(os.path.join(translations_path, 'alert_monitoring/api/boot/resources/i18n'))

    @patch.object(CatalogService, CatalogService.sync_catalog.__name__)
    def test_should_sync_catalog_and_return_201(self, mock_sync):
        """
        Given valid request
        When POST /catalog/sync
        Then should return 201 with count of synced items
        """
        mock_sync.return_value = 15

        response = self.client.post('/catalog/sync')

        assert response.status_code == 201
        data = response.json()
        assert data['synced'] == 15
        assert 'message' in data

    @patch.object(CatalogService, CatalogService.get_all_catalog_apps.__name__)
    def test_should_get_catalog_apps_and_return_200(self, mock_get):
        """
        Given catalog apps exist
        When GET /catalog
        Then should return list of catalog apps
        """
        mock_get.return_value = [
            CatalogApp(object_id='1', name='My-App', csw_code='CSW001'),
        ]

        response = self.client.get('/catalog')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'My-App'

    @patch.object(CatalogService, CatalogService.get_all_catalog_apps.__name__)
    def test_should_pass_name_filter_to_catalog_service(self, mock_get):
        """
        Given name query param
        When GET /catalog?name=my-app
        Then should return filtered catalog apps
        """
        mock_get.return_value = []

        response = self.client.get('/catalog?name=my-app')

        assert response.status_code == 200
        mock_get.assert_called_once_with(name='my-app')

    @patch.object(CatalogService, CatalogService.get_all_catalog_apps.__name__)
    def test_catalog_returns_empty_list_when_no_apps(self, mock_get):
        """
        Given no apps in catalog
        When GET /catalog
        Then should return empty list
        """
        mock_get.return_value = []

        response = self.client.get('/catalog')

        assert response.status_code == 200
        assert response.json() == []


class TestAlertApiControllerAdapter:

    @classmethod
    def setup_class(cls):
        cls.app = FastAPIBuilder()
        add_session_middleware(cls.app)
        set_i18n()
        cls.client = TestClient(cls.app)
        translations_path = Path(os.path.dirname(__file__)).parent.parent.parent.parent.parent.parent
        load_translations(os.path.join(translations_path, 'alert_monitoring/api/boot/resources/i18n'))

    @patch.object(AlertApiService, AlertApiService.sync_alert_apis.__name__)
    def test_should_sync_alert_api_rules_and_return_201(self, mock_sync):
        """
        Given valid request
        When POST /alert-api/sync
        Then should return 201 with count of saved rules
        """
        mock_sync.return_value = 20

        response = self.client.post('/alert-api/sync')

        assert response.status_code == 201
        data = response.json()
        assert data['saved'] == 20
        assert 'message' in data

    @patch.object(AlertApiService, AlertApiService.get_apis.__name__)
    def test_should_get_distinct_apis(self, mock_get):
        """
        Given APIs exist
        When GET /alert-api/apis
        Then should return list of API names
        """
        mock_get.return_value = ['absence', 'employee', 'payroll']

        response = self.client.get('/alert-api/apis')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert 'absence' in data

    @patch.object(AlertApiService, AlertApiService.get_alert_apis.__name__)
    def test_should_get_alert_api_rules(self, mock_get):
        """
        Given alert API rules exist
        When GET /alert-api
        Then should return list of rules
        """
        mock_get.return_value = [
            AlertApi(rule_id='rule-1', name='Errores 500 absence', apis_alertadas=['absence'])
        ]

        response = self.client.get('/alert-api')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['rule_id'] == 'rule-1'

    @patch.object(AlertApiService, AlertApiService.get_alert_apis.__name__)
    def test_should_pass_api_filter(self, mock_get):
        """
        Given api query param
        When GET /alert-api?api=absence
        Then should pass filter to service
        """
        mock_get.return_value = []

        response = self.client.get('/alert-api?api=absence')

        assert response.status_code == 200
        mock_get.assert_called_once_with(api='absence')


class TestCatalogAppApiControllerAdapter:

    @classmethod
    def setup_class(cls):
        cls.app = FastAPIBuilder()
        add_session_middleware(cls.app)
        set_i18n()
        cls.client = TestClient(cls.app)
        translations_path = Path(os.path.dirname(__file__)).parent.parent.parent.parent.parent.parent
        load_translations(os.path.join(translations_path, 'alert_monitoring/api/boot/resources/i18n'))

    @patch.object(CatalogAppApiService, CatalogAppApiService.sync_catalog_app_api.__name__)
    def test_should_sync_catalog_app_api_and_return_201(self, mock_sync):
        """
        Given valid request
        When POST /catalog-api/sync
        Then should return 201 with count of synced items
        """
        mock_sync.return_value = 8

        response = self.client.post('/catalog-api/sync')

        assert response.status_code == 201
        data = response.json()
        assert data['synced'] == 8

    @patch.object(CatalogAppApiService, CatalogAppApiService.get_all.__name__)
    def test_should_get_catalog_app_api_and_return_200(self, mock_get):
        """
        Given catalog app-api entries exist
        When GET /catalog-api
        Then should return list of entries
        """
        mock_get.return_value = [
            CatalogAppApi(app='my-app', microservice='my-app-back', apis=['absence'])
        ]

        response = self.client.get('/catalog-api')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['app'] == 'my-app'

    @patch.object(CatalogAppApiService, CatalogAppApiService.get_all.__name__)
    def test_should_pass_app_filter(self, mock_get):
        """
        Given app query param
        When GET /catalog-api?app=my-app
        Then should pass filter to service
        """
        mock_get.return_value = []

        response = self.client.get('/catalog-api?app=my-app')

        assert response.status_code == 200
        mock_get.assert_called_once_with(app='my-app')
