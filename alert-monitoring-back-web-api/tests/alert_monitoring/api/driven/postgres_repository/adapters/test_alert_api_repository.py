import pytest

from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.driven.postgres_repository.adapters.alert_api_repository import AlertApiRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.models.alert_api_model import AlertApiDB


@pytest.fixture
def adapter(mocker):
    return AlertApiRepositoryAdapter(
        sqlalchemy_repository=mocker.MagicMock(),
        alert_api_db_mapper=mocker.MagicMock(),
        logger=mocker.MagicMock(),
    )


class TestAlertApiRepositoryAdapterSaveAll:

    def test_maps_and_adds_each_rule_then_commits(self, adapter):
        """
        Given a list of API alert rules
        When save_all is called
        Then it should map and add each rule to the session and commit once
        """
        rules = [AlertApi(rule_id='1', name='rule a'), AlertApi(rule_id='2', name='rule b')]
        db_rows = [AlertApiDB(rule_id='1', name='rule a'), AlertApiDB(rule_id='2', name='rule b')]
        adapter.alert_api_db_mapper.to_db.side_effect = db_rows

        adapter.save_all(rules)

        assert adapter.sqlalchemy_repository.add.call_count == 2
        adapter.sqlalchemy_repository.add.assert_any_call(db_rows[0])
        adapter.sqlalchemy_repository.add.assert_any_call(db_rows[1])
        adapter.sqlalchemy_repository.commit.assert_called_once()


class TestAlertApiRepositoryAdapterDeleteAll:

    def test_deletes_all_rows_and_commits(self, adapter):
        """
        Given existing API alert rules
        When delete_all is called
        Then it should delete all rows and commit
        """
        adapter.sqlalchemy_repository.query.return_value.delete.return_value = 3

        adapter.delete_all()

        adapter.sqlalchemy_repository.query.assert_called_once_with(AlertApiDB)
        adapter.sqlalchemy_repository.commit.assert_called_once()


class TestAlertApiRepositoryAdapterGetAll:

    def test_returns_all_rules_when_no_api_filter(self, adapter):
        """
        Given no api filter
        When get_all is called
        Then it should query without filtering and map the rows to domain
        """
        rows = [AlertApiDB(rule_id='1', name='rule a')]
        adapter.sqlalchemy_repository.query.return_value.all.return_value = rows
        adapter.alert_api_db_mapper.to_domain_list.return_value = [AlertApi(rule_id='1', name='rule a')]

        result = adapter.get_all()

        assert len(result) == 1
        adapter.sqlalchemy_repository.query.assert_called_once_with(AlertApiDB)
        adapter.alert_api_db_mapper.to_domain_list.assert_called_once_with(rows)

    def test_filters_by_api_when_provided(self, adapter):
        """
        Given an api filter
        When get_all is called
        Then it should apply the JSONB contains filter before mapping the results
        """
        rows = [AlertApiDB(rule_id='1', name='rule a', apis_alertadas=['payroll'])]
        adapter.sqlalchemy_repository.query.return_value.filter.return_value.all.return_value = rows
        adapter.alert_api_db_mapper.to_domain_list.return_value = [
            AlertApi(rule_id='1', name='rule a', apis_alertadas=['payroll'])
        ]

        result = adapter.get_all(api='payroll')

        assert len(result) == 1
        adapter.alert_api_db_mapper.to_domain_list.assert_called_once_with(rows)


class TestAlertApiRepositoryAdapterGetDistinctApis:

    def test_returns_distinct_api_names_from_the_raw_rows(self, adapter):
        """
        Given the database returns rows of (value,) tuples
        When get_distinct_apis is called
        Then it should return the first column of each row as a flat list
        """
        adapter.sqlalchemy_repository.execute.return_value = [('absence',), ('payroll',)]

        result = adapter.get_distinct_apis()

        assert result == ['absence', 'payroll']
        adapter.sqlalchemy_repository.execute.assert_called_once()
