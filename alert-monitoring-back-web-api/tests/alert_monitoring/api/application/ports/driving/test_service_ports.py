import pytest

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driving.catalog_service_port import CatalogServicePort
from alert_monitoring.api.application.ports.driving.catalog_app_api_service_port import CatalogAppApiServicePort


class _FakeAlertService(AlertServicePort):
    def sync_prometheus_alerts(self):
        return super().sync_prometheus_alerts()

    def sync_elastic_alerts(self):
        return super().sync_elastic_alerts()

    def get_all_alerts(self, filters=None):
        return super().get_all_alerts(filters)

    def get_active_blackouts(self, solution=None):
        return super().get_active_blackouts(solution)

    def get_default_alerts(self):
        return super().get_default_alerts()

    def get_solution_view(self, solution):
        return super().get_solution_view(solution)

    def get_api_solution_view(self, app):
        return super().get_api_solution_view(app)


class _FakeCatalogService(CatalogServicePort):
    def sync_catalog(self):
        return super().sync_catalog()

    def get_all_catalog_apps(self, name=None):
        return super().get_all_catalog_apps(name)


class _FakeCatalogAppApiService(CatalogAppApiServicePort):
    def sync_catalog_app_api(self):
        return super().sync_catalog_app_api()

    def get_all(self, app=None):
        return super().get_all(app)


class TestDrivingServicePortsDefaultBehaviour:

    @pytest.mark.parametrize(
        "instance, method_name, method_args",
        [
            (_FakeAlertService(), "sync_prometheus_alerts", ()),
            (_FakeAlertService(), "sync_elastic_alerts", ()),
            (_FakeAlertService(), "get_all_alerts", (None,)),
            (_FakeAlertService(), "get_active_blackouts", (None,)),
            (_FakeAlertService(), "get_default_alerts", ()),
            (_FakeAlertService(), "get_solution_view", ("my-solution",)),
            (_FakeAlertService(), "get_api_solution_view", ("my-app",)),
            (_FakeCatalogService(), "sync_catalog", ()),
            (_FakeCatalogService(), "get_all_catalog_apps", (None,)),
            (_FakeCatalogAppApiService(), "sync_catalog_app_api", ()),
            (_FakeCatalogAppApiService(), "get_all", (None,)),
        ],
    )
    def test_abstract_method_bodies_are_noop(self, instance, method_name, method_args):
        """
        Given a concrete service implementation that delegates to the abstract body
        When the inherited abstract method is invoked via super()
        Then it should return None, since driving ports declare their contract with a no-op body
        """
        method = getattr(instance, method_name)

        assert method(*method_args) is None
