import pytest

from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_repository import CatalogAppRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_model import CatalogAppDB


@pytest.fixture
def adapter(mocker):
    return CatalogAppRepositoryAdapter(
        sqlalchemy_repository=mocker.MagicMock(),
        catalog_app_db_mapper=mocker.MagicMock(),
        logger=mocker.MagicMock(),
    )


class TestCatalogAppRepositoryAdapterSaveAll:

    def test_reconciles_apps_by_object_id(self, adapter, mocker):
        """
        Given a list of catalog apps
        When save_all is called
        Then it should reconcile CatalogAppDB rows keyed by object_id using the _apply mapping
        """
        mock_reconcile = mocker.patch(
            'alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_repository.reconcile_by_key'
        )
        apps = [CatalogApp(object_id='1', name='my-app')]

        adapter.save_all(apps)

        mock_reconcile.assert_called_once_with(
            adapter.sqlalchemy_repository,
            CatalogAppDB,
            apps,
            key_attr="object_id",
            apply_fn=adapter._apply,
        )

    def test_apply_copies_domain_fields_onto_db_row(self):
        """
        Given a CatalogAppDB row and a CatalogApp domain object
        When _apply is called
        Then it should copy object_id, name and csw_code onto the row
        """
        row = CatalogAppDB()
        app = CatalogApp(object_id='42', name='my-app', csw_code='CSW-1')

        CatalogAppRepositoryAdapter._apply(row, app)

        assert row.object_id == '42'
        assert row.name == 'my-app'
        assert row.csw_code == 'CSW-1'


class TestCatalogAppRepositoryAdapterGetAll:

    def test_returns_all_apps_when_no_name_filter(self, adapter):
        """
        Given no name filter
        When get_all is called
        Then it should query without filtering and map the ordered rows to domain
        """
        rows = [CatalogAppDB(object_id='1', name='my-app')]
        adapter.sqlalchemy_repository.query.return_value.order_by.return_value.all.return_value = rows
        adapter.catalog_app_db_mapper.to_domain_list.return_value = [CatalogApp(object_id='1', name='my-app')]

        result = adapter.get_all()

        assert len(result) == 1
        adapter.sqlalchemy_repository.query.assert_called_once_with(CatalogAppDB)
        adapter.catalog_app_db_mapper.to_domain_list.assert_called_once_with(rows)

    def test_filters_by_name_when_provided(self, adapter):
        """
        Given a name filter
        When get_all is called
        Then it should apply the ilike filter before mapping the results
        """
        rows = [CatalogAppDB(object_id='1', name='my-app')]
        adapter.sqlalchemy_repository.query.return_value.filter.return_value.order_by.return_value.all.return_value = rows
        adapter.catalog_app_db_mapper.to_domain_list.return_value = [CatalogApp(object_id='1', name='my-app')]

        result = adapter.get_all(name='my')

        assert len(result) == 1
        adapter.catalog_app_db_mapper.to_domain_list.assert_called_once_with(rows)
