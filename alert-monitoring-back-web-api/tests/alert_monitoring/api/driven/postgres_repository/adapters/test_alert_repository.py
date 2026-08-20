import pytest

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.driven.postgres_repository.adapters.alert_repository import AlertRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.models.alert_model import AlertDB


def _alert_db(**overrides):
    fields = dict(name='alert', description='desc', source_tool='Prometheus', severity='critical')
    fields.update(overrides)
    return AlertDB(**fields)


@pytest.fixture
def adapter(mocker):
    return AlertRepositoryAdapter(
        sqlalchemy_repository=mocker.MagicMock(),
        alert_db_mapper=mocker.MagicMock(),
        logger=mocker.MagicMock(),
    )


class TestAlertRepositoryAdapterSaveAll:

    def test_maps_and_adds_each_alert_then_commits(self, adapter):
        """
        Given a list of alerts
        When save_all is called
        Then it should map and add each alert to the session and commit once
        """
        alerts = [Alert(name='a1', description='d1', severity='critical'),
                  Alert(name='a2', description='d2', severity='warning')]
        db_rows = [_alert_db(name='a1'), _alert_db(name='a2')]
        adapter.alert_db_mapper.to_db.side_effect = db_rows

        adapter.save_all(alerts)

        assert adapter.sqlalchemy_repository.add.call_count == 2
        adapter.sqlalchemy_repository.add.assert_any_call(db_rows[0])
        adapter.sqlalchemy_repository.add.assert_any_call(db_rows[1])
        adapter.sqlalchemy_repository.commit.assert_called_once()


class TestAlertRepositoryAdapterDeleteBySourceTool:

    def test_deletes_matching_rows_and_commits(self, adapter):
        """
        Given a source_tool
        When delete_by_source_tool is called
        Then it should filter by source_tool, delete the matching rows and commit
        """
        adapter.sqlalchemy_repository.query.return_value.filter.return_value.delete.return_value = 2

        adapter.delete_by_source_tool('Prometheus')

        adapter.sqlalchemy_repository.query.assert_called_once_with(AlertDB)
        adapter.sqlalchemy_repository.commit.assert_called_once()


class TestAlertRepositoryAdapterGetAll:

    def test_returns_all_rows_when_no_filters(self, adapter):
        """
        Given no filters
        When get_all is called
        Then it should query without filtering and map the rows to domain
        """
        rows = [_alert_db()]
        adapter.sqlalchemy_repository.query.return_value.all.return_value = rows
        adapter.alert_db_mapper.to_domain_list.return_value = [Alert(name='alert', description='desc', severity='critical')]

        result = adapter.get_all()

        assert len(result) == 1
        adapter.sqlalchemy_repository.query.assert_called_once_with(AlertDB)
        adapter.alert_db_mapper.to_domain_list.assert_called_once_with(rows)

    def test_returns_all_rows_when_filters_object_is_empty(self, adapter):
        """
        Given an AlertFilter with every field unset
        When get_all is called
        Then it should not apply any filter clause
        """
        query_mock = adapter.sqlalchemy_repository.query.return_value
        rows = [_alert_db()]
        query_mock.all.return_value = rows
        adapter.alert_db_mapper.to_domain_list.return_value = [Alert(name='alert', description='desc', severity='critical')]

        result = adapter.get_all(filters=AlertFilter())

        assert len(result) == 1
        query_mock.filter.assert_not_called()

    def test_applies_a_filter_clause_per_provided_field(self, adapter):
        """
        Given an AlertFilter with name, source_tool, severity, microservice and solution set
        When get_all is called
        Then it should chain one filter clause per provided field
        """
        query_mock = adapter.sqlalchemy_repository.query.return_value
        query_mock.filter.return_value = query_mock
        rows = [_alert_db()]
        query_mock.all.return_value = rows
        adapter.alert_db_mapper.to_domain_list.return_value = [Alert(name='alert', description='desc', severity='critical')]

        filters = AlertFilter(
            name='alert', source_tool='Prometheus', severity='critical',
            microservice='my-back', solution='PI-1',
        )

        result = adapter.get_all(filters=filters)

        assert len(result) == 1
        assert query_mock.filter.call_count == 5

    def test_filters_out_rows_without_a_wanted_environment(self, adapter):
        """
        Given an AlertFilter restricted to certain environments
        When get_all is called
        Then it should keep only rows whose environments intersect the wanted set
        """
        matching_row = _alert_db(name='matching', environments=['pro'])
        other_env_row = _alert_db(name='other-env', environments=['dev'])
        no_env_row = _alert_db(name='no-env', environments=[])
        adapter.sqlalchemy_repository.query.return_value.all.return_value = [
            matching_row, other_env_row, no_env_row,
        ]
        adapter.alert_db_mapper.to_domain_list.return_value = [
            Alert(name='matching', description='desc', severity='critical', environments=['pro'])
        ]

        adapter.get_all(filters=AlertFilter(environments=['pro']))

        adapter.alert_db_mapper.to_domain_list.assert_called_once_with([matching_row])
