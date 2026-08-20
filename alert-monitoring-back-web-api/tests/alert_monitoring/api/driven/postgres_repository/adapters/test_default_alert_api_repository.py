import pytest

from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_api_repository import DefaultAlertApiRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.models.default_alert_api_model import DefaultAlertApiDB


@pytest.fixture
def adapter(mocker):
    return DefaultAlertApiRepositoryAdapter(
        sqlalchemy_repository=mocker.MagicMock(),
        default_alert_api_db_mapper=mocker.MagicMock(),
        logger=mocker.MagicMock(),
    )


class TestDefaultAlertApiRepositoryAdapterGetAll:

    def test_returns_ordered_rows_mapped_to_domain(self, adapter):
        """
        Given rows exist in default_alert_api
        When get_all is called
        Then it should query ordered by id and map the rows to domain
        """
        rows = [DefaultAlertApiDB(raw_name='r1', display_name='R1')]
        adapter.sqlalchemy_repository.query.return_value.order_by.return_value.all.return_value = rows
        adapter.mapper.to_domain_list.return_value = [DefaultAlertApi(raw_name='r1', display_name='R1')]

        result = adapter.get_all()

        assert len(result) == 1
        adapter.sqlalchemy_repository.query.assert_called_once_with(DefaultAlertApiDB)
        adapter.mapper.to_domain_list.assert_called_once_with(rows)


class TestDefaultAlertApiRepositoryAdapterUpsertBatch:

    def test_delegates_to_upsert_preserving_display(self, adapter, mocker):
        """
        Given a batch of default alert APIs
        When upsert_batch is called
        Then it should delegate to upsert_preserving_display with Kibana-owned fields
        """
        mock_upsert = mocker.patch(
            'alert_monitoring.api.driven.postgres_repository.adapters.default_alert_api_repository.upsert_preserving_display'
        )
        alerts = [DefaultAlertApi(
            raw_name='r1',
            display_name='R1',
            raw_description='desc',
            excluded_apis=['api-a'],
        )]

        adapter.upsert_batch(alerts)

        mock_upsert.assert_called_once()
        args, kwargs = mock_upsert.call_args
        assert args == (adapter.sqlalchemy_repository, DefaultAlertApiDB, alerts)
        owned_fields = kwargs['owned_fields'](alerts[0])
        assert owned_fields == {
            "raw_description": "desc",
            "excluded_apis": ["api-a"],
        }


class TestDefaultAlertApiRepositoryAdapterDeleteWhereNotIn:

    def test_deletes_rows_not_in_the_given_raw_names(self, adapter):
        """
        Given a list of currently active raw_names
        When delete_where_not_in is called
        Then it should filter out obsolete rows, delete them and commit
        """
        adapter.delete_where_not_in(['r1', 'r2'])

        adapter.sqlalchemy_repository.query.return_value.filter.return_value.delete.assert_called_once_with(
            synchronize_session=False
        )
        adapter.sqlalchemy_repository.commit.assert_called_once()

    def test_deletes_all_rows_when_raw_names_is_empty(self, adapter):
        """
        Given an empty list of active raw_names
        When delete_where_not_in is called
        Then it should delete without filtering (nothing is currently active) and commit
        """
        adapter.delete_where_not_in([])

        adapter.sqlalchemy_repository.query.return_value.filter.assert_not_called()
        adapter.sqlalchemy_repository.query.return_value.delete.assert_called_once_with(synchronize_session=False)
        adapter.sqlalchemy_repository.commit.assert_called_once()
