import pytest
from unittest.mock import MagicMock

from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_repository import CatalogAppRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.mappers.catalog_app_db_mapper import CatalogAppDBMapper


def _make_app(**kwargs) -> CatalogApp:
    defaults = dict(object_id="obj-1", name="my-app", csw_code="CSW001")
    defaults.update(kwargs)
    return CatalogApp(**defaults)


@pytest.mark.integration
class TestCatalogAppRepositoryIntegration:

    @pytest.fixture
    def repo(self, db_session):
        return CatalogAppRepositoryAdapter(
            sqlalchemy_repository=db_session,
            catalog_app_db_mapper=CatalogAppDBMapper(),
            logger=MagicMock(),
        )

    def test_save_and_retrieve_apps(self, repo):
        """Guardar varias apps y recuperarlas todas."""
        repo.save_all([
            _make_app(object_id="obj-1", name="app-one"),
            _make_app(object_id="obj-2", name="app-two"),
        ])

        results = repo.get_all()

        assert len(results) == 2
        assert {a.name for a in results} == {"app-one", "app-two"}

    def test_reconcile_updates_name_for_existing_object_id(self, repo):
        """Una segunda sincronización con el mismo object_id actualiza el nombre."""
        repo.save_all([_make_app(object_id="obj-1", name="old-name")])
        repo.save_all([_make_app(object_id="obj-1", name="new-name")])

        results = repo.get_all()

        assert len(results) == 1
        assert results[0].name == "new-name"

    def test_reconcile_deletes_app_not_in_new_batch(self, repo):
        """Una app que no aparece en la nueva sincronización se elimina de la tabla."""
        repo.save_all([
            _make_app(object_id="obj-1", name="app-one"),
            _make_app(object_id="obj-2", name="app-two"),
        ])

        repo.save_all([_make_app(object_id="obj-1", name="app-one")])

        results = repo.get_all()
        assert len(results) == 1
        assert results[0].object_id == "obj-1"

    def test_reconcile_with_empty_batch_clears_all_apps(self, repo):
        """Una sincronización con lista vacía elimina todas las apps del catálogo."""
        repo.save_all([_make_app(object_id="obj-1", name="app-one")])

        repo.save_all([])

        assert repo.get_all() == []

    def test_get_all_with_name_filter_is_case_insensitive(self, repo):
        """El filtro por nombre es insensible a mayúsculas."""
        repo.save_all([
            _make_app(object_id="obj-1", name="OrderService"),
            _make_app(object_id="obj-2", name="PaymentService"),
        ])

        results = repo.get_all(name="order")

        assert len(results) == 1
        assert results[0].name == "OrderService"

    def test_get_all_with_name_filter_partial_match(self, repo):
        """El filtro por nombre es parcial: 'Service' devuelve todas las que lo contienen."""
        repo.save_all([
            _make_app(object_id="obj-1", name="OrderService"),
            _make_app(object_id="obj-2", name="PaymentService"),
            _make_app(object_id="obj-3", name="Catalog"),
        ])

        results = repo.get_all(name="Service")

        assert len(results) == 2
        assert {a.name for a in results} == {"OrderService", "PaymentService"}

    def test_get_all_returns_results_ordered_alphabetically_by_name(self, repo):
        """Los resultados se devuelven ordenados por nombre."""
        repo.save_all([
            _make_app(object_id="obj-3", name="Zebra"),
            _make_app(object_id="obj-1", name="Alpha"),
            _make_app(object_id="obj-2", name="Mango"),
        ])

        results = repo.get_all()

        assert [a.name for a in results] == ["Alpha", "Mango", "Zebra"]

    def test_save_persists_csw_code(self, repo):
        """El csw_code se almacena y se recupera correctamente."""
        repo.save_all([_make_app(object_id="obj-1", name="my-app", csw_code="CSW999")])

        results = repo.get_all()

        assert results[0].csw_code == "CSW999"
