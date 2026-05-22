import pytest

from alert_monitoring.api.driven.kibana_repository.mappers.kibana_rule_mapper import KibanaRuleMapper
from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig


@pytest.fixture
def mapper():
    return KibanaRuleMapper()


@pytest.fixture
def base_config():
    return KibanaConfig(name="test-kibana", base_url="https://kibana.example.com", api_key="test-key", space_id="api-management")


def _raw_rule(name: str, tags: list, kql: str = "", actions: list = None) -> dict:
    return {
        "id": "abc-123",
        "enabled": True,
        "name": name,
        "tags": tags,
        "schedule": {"interval": "2m"},
        "actions": actions or [],
        "params": {
            "searchConfiguration": {
                "query": {"query": kql, "language": "kuery"}
            }
        },
        "execution_status": {"status": "ok", "last_execution_date": "2026-05-22T07:00:00Z"},
    }


class TestNameCleaning:
    def test_global_prefix_is_stripped_from_name(self, mapper, base_config):
        """
        Given a rule whose name starts with '[Global]'
        When mapped
        Then the name has the prefix removed
        """
        raw = _raw_rule("[Global] Errores Totales 15% OCP", tags=["global"])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.name == "Errores Totales 15% OCP"

    def test_global_prefix_stripped_case_insensitive(self, mapper, base_config):
        raw = _raw_rule("[global] Some Rule", tags=["global"])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.name == "Some Rule"

    def test_non_global_prefix_is_preserved(self, mapper, base_config):
        raw = _raw_rule("[Absence] Errores 500", tags=["api-mngt"])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.name == "[Absence] Errores 500"


class TestIsGlobal:
    def test_global_tag_marks_rule_as_global(self, mapper, base_config):
        """
        Given a rule with tag 'global' and no APIs in KQL
        When mapped
        Then is_global is True
        """
        raw = _raw_rule("[Global] Errores Totales 15% OCP", tags=["global", "api-mngt"])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.is_global is True

    def test_global_tag_marks_rule_as_global_even_with_exclusion_list(self, mapper, base_config):
        """
        Given a rule with tag 'global' whose KQL uses NOT exclusions
        When mapped
        Then is_global is True (tag wins, exclusion list does not pollute is_global)
        """
        kql = (
            'alerta500.keyword: "true" AND ('
            'NOT transactionElement.serviceName: payroll AND '
            'NOT transactionElement.serviceName: absence AND '
            'NOT transactionElement.serviceName: suppliers)'
        )
        raw = _raw_rule("[Global] Errores 500 por API y método", tags=["api-mngt", "global"], kql=kql)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.is_global is True

    def test_rule_without_global_tag_is_not_global(self, mapper, base_config):
        """
        Given a rule without tag 'global'
        When mapped
        Then is_global is False
        """
        kql = 'alerta500.keyword: "true" AND transactionElement.serviceName: ("absence" OR "employee-labor-absence")'
        raw = _raw_rule("[Absence] Errores 500", tags=["api-mngt"], kql=kql)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.is_global is False


class TestExtractApis:
    def test_extracts_apis_from_positive_kql(self, mapper, base_config):
        """
        Given a KQL with explicit positive serviceName filters
        When mapped
        Then apis contains only those services
        """
        kql = (
            'alerta500.keyword: "true" AND transactionElement.serviceName: ('
            '"absence" OR "employee-labor-absence" OR "employee-labor-absence-entitlement")'
        )
        raw = _raw_rule("[Absence] Errores 500", tags=["api-mngt"], kql=kql)
        result = mapper.to_domain([raw], base_config)[0]
        assert "absence" in result.apis

    def test_does_not_extract_negated_apis_as_targeted_apis(self, mapper, base_config):
        """
        Given a KQL with only NOT exclusions (global exclusion list pattern)
        When mapped
        Then apis is empty because no API is positively targeted
        """
        kql = (
            'alerta500.keyword: "true" AND ('
            'NOT transactionElement.serviceName: payroll AND '
            'NOT transactionElement.serviceName: absence AND '
            'NOT transactionElement.serviceName: suppliers)'
        )
        raw = _raw_rule("[Global] Errores 500 por API y método", tags=["api-mngt", "global"], kql=kql)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.apis == []

    def test_excludes_negated_apis_from_positive_matches(self, mapper, base_config):
        """
        Given a KQL that positively matches a serviceName but also negates others
        When mapped
        Then apis only contains the positively targeted service
        """
        kql = (
            'alerta500.keyword: "true" AND '
            'transactionElement.serviceName: my-api AND '
            'NOT transactionElement.serviceName: other-api'
        )
        raw = _raw_rule("[Team] Errores 500 my-api", tags=["api-mngt"], kql=kql)
        result = mapper.to_domain([raw], base_config)[0]
        assert "my-api" in result.apis
        assert "other-api" not in result.apis

    def test_esql_rule_has_empty_apis(self, mapper, base_config):
        """
        Given a rule using esqlQuery (no searchConfiguration)
        When mapped
        Then apis is empty
        """
        raw = {
            "id": "esql-rule-1",
            "enabled": True,
            "name": "[Global] Errores Totales 15% OCP",
            "tags": ["global", "api-mngt"],
            "schedule": {"interval": "2m"},
            "actions": [],
            "params": {
                "searchType": "esqlQuery",
                "esqlQuery": {"esql": "FROM logs-otel | STATS total = COUNT(*)"},
            },
            "execution_status": {"status": "ok", "last_execution_date": "2026-05-22T07:00:00Z"},
        }
        result = mapper.to_domain([raw], base_config)[0]
        assert result.apis == []
        assert result.is_global is True
