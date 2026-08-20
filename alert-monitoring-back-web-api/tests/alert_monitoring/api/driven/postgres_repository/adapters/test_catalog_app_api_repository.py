import pytest

from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi
from alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_api_repository import CatalogAppApiRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_api_model import CatalogAppApiDB


@pytest.fixture
def adapter(mocker):
    return CatalogAppApiRepositoryAdapter(
        sqlalchemy_repository=mocker.MagicMock(),
        catalog_app_api_db_mapper=mocker.MagicMock(),
        logger=mocker.MagicMock(),
    )


class TestCatalogAppApiRepositoryAdapterReplaceAll:

    def test_reconciles_entries_by_microservice(self, adapter, mocker):
        """
        Given a list of catalog app APIs
        When replace_all is called
        Then it should reconcile CatalogAppApiDB rows keyed by microservice using the _apply mapping
        """
        mock_reconcile = mocker.patch(
            'alert_monitoring.api.driven.postgres_repository.adapters.catalog_app_api_repository.reconcile_by_key'
        )
        items = [CatalogAppApi(app='my-app', microservice='my-back', apis=['api-a'])]

        adapter.replace_all(items)

        mock_reconcile.assert_called_once_with(
            adapter.sqlalchemy_repository,
            CatalogAppApiDB,
            items,
            key_attr="microservice",
            apply_fn=adapter._apply,
        )

    def test_apply_copies_domain_fields_onto_db_row(self):
        """
        Given a CatalogAppApiDB row and a CatalogAppApi domain object
        When _apply is called
        Then it should copy microservice, app and apis onto the row
        """
        row = CatalogAppApiDB()
        item = CatalogAppApi(app='my-app', microservice='my-back', apis=['api-a', 'api-b'])

        CatalogAppApiRepositoryAdapter._apply(row, item)

        assert row.microservice == 'my-back'
        assert row.app == 'my-app'
        assert row.apis == ['api-a', 'api-b']


class TestCatalogAppApiRepositoryAdapterGetAll:

    def test_returns_all_entries_when_no_app_filter(self, adapter):
        """
        Given no app filter
        When get_all is called
        Then it should query without filtering and map the ordered rows to domain
        """
        rows = [CatalogAppApiDB(app='my-app', microservice='my-back', apis=['api-a'])]
        adapter.sqlalchemy_repository.query.return_value.order_by.return_value.all.return_value = rows
        adapter.mapper.to_domain_list.return_value = [CatalogAppApi(app='my-app', microservice='my-back', apis=['api-a'])]

        result = adapter.get_all()

        assert len(result) == 1
        adapter.sqlalchemy_repository.query.assert_called_once_with(CatalogAppApiDB)
        adapter.mapper.to_domain_list.assert_called_once_with(rows)

    def test_filters_by_app_when_provided(self, adapter):
        """
        Given an app filter
        When get_all is called
        Then it should apply the ilike filter before mapping the results
        """
        rows = [CatalogAppApiDB(app='my-app', microservice='my-back', apis=['api-a'])]
        adapter.sqlalchemy_repository.query.return_value.filter.return_value.order_by.return_value.all.return_value = rows
        adapter.mapper.to_domain_list.return_value = [CatalogAppApi(app='my-app', microservice='my-back', apis=['api-a'])]

        result = adapter.get_all(app='my')

        assert len(result) == 1
        adapter.mapper.to_domain_list.assert_called_once_with(rows)
