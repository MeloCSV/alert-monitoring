import pytest

from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_repository import DefaultAlertRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.models.default_alert_model import DefaultAlertDB


@pytest.fixture
def adapter(mocker):
    return DefaultAlertRepositoryAdapter(
        sqlalchemy_repository=mocker.MagicMock(),
        default_alert_db_mapper=mocker.MagicMock(),
        logger=mocker.MagicMock(),
    )


class TestDefaultAlertRepositoryAdapterGetAll:

    def test_returns_ordered_rows_mapped_to_domain(self, adapter):
        """
        Given rows exist in default_alert_app
        When get_all is called
        Then it should query ordered by id and map the rows to domain
        """
        rows = [DefaultAlertDB(raw_name='r1', display_name='R1')]
        adapter.sqlalchemy_repository.query.return_value.order_by.return_value.all.return_value = rows
        adapter.mapper.to_domain_list.return_value = [DefaultAlert(raw_name='r1', display_name='R1')]

        result = adapter.get_all()

        assert len(result) == 1
        adapter.sqlalchemy_repository.query.assert_called_once_with(DefaultAlertDB)
        adapter.mapper.to_domain_list.assert_called_once_with(rows)


class TestDefaultAlertRepositoryAdapterUpsertBatch:

    def test_delegates_to_upsert_preserving_display(self, adapter, mocker):
        """
        Given a batch of default alerts
        When upsert_batch is called
        Then it should delegate to upsert_preserving_display with Prometheus-owned fields
        """
        mock_upsert = mocker.patch(
            'alert_monitoring.api.driven.postgres_repository.adapters.default_alert_repository.upsert_preserving_display'
        )
        alerts = [DefaultAlert(
            raw_name='r1',
            display_name='R1',
            raw_description='desc',
            excluded_namespaces=['ns-a'],
            included_namespaces=['ns-b'],
            excluded_jobs=['job-a'],
        )]

        adapter.upsert_batch(alerts)

        mock_upsert.assert_called_once()
        args, kwargs = mock_upsert.call_args
        assert args == (adapter.sqlalchemy_repository, DefaultAlertDB, alerts)
        owned_fields = kwargs['owned_fields'](alerts[0])
        assert owned_fields == {
            "raw_description": "desc",
            "excluded_namespaces": ["ns-a"],
            "included_namespaces": ["ns-b"],
            "excluded_jobs": ["job-a"],
        }
