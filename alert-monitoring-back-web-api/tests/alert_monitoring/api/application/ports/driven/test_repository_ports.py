import pytest

from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_api_repository_port import CatalogAppApiRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort


class _FakeAlertRepository(AlertRepositoryPort):
    def save_all(self, alerts):
        return super().save_all(alerts)

    def delete_by_source_tool(self, source_tool):
        return super().delete_by_source_tool(source_tool)

    def get_all(self, filters=None):
        return super().get_all(filters)


class _FakeCatalogAppRepository(CatalogAppRepositoryPort):
    def save_all(self, apps):
        return super().save_all(apps)

    def get_all(self, name=None):
        return super().get_all(name)


class _FakeCatalogAppApiRepository(CatalogAppApiRepositoryPort):
    def replace_all(self, items):
        return super().replace_all(items)

    def get_all(self, app=None):
        return super().get_all(app)


class _FakeDefaultAlertRepository(DefaultAlertRepositoryPort):
    def get_all(self):
        return super().get_all()

    def upsert_batch(self, alerts):
        return super().upsert_batch(alerts)


class TestDrivenRepositoryPortsDefaultBehaviour:

    @pytest.mark.parametrize(
        "instance, method_name, method_args",
        [
            (_FakeAlertRepository(), "save_all", ([],)),
            (_FakeAlertRepository(), "delete_by_source_tool", ("Prometheus",)),
            (_FakeAlertRepository(), "get_all", (None,)),
            (_FakeCatalogAppRepository(), "save_all", ([],)),
            (_FakeCatalogAppRepository(), "get_all", (None,)),
            (_FakeCatalogAppApiRepository(), "replace_all", ([],)),
            (_FakeCatalogAppApiRepository(), "get_all", (None,)),
            (_FakeDefaultAlertRepository(), "get_all", ()),
            (_FakeDefaultAlertRepository(), "upsert_batch", ([],)),
        ],
    )
    def test_abstract_method_bodies_are_noop(self, instance, method_name, method_args):
        """
        Given a concrete port implementation that delegates to the abstract body
        When the inherited abstract method is invoked via super()
        Then it should return None, since driven ports declare their contract with a no-op body
        """
        method = getattr(instance, method_name)

        assert method(*method_args) is None
