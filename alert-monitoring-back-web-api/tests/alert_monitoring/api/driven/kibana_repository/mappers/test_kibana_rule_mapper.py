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
        raw = _raw_rule("[Global] Errores Totales 15% OCP", tags=["global"])
        defaults, _ = mapper.to_domain_split([raw], base_config)
        assert defaults[0].name == "Errores Totales 15% OCP"

    def test_global_prefix_stripped_case_insensitive(self, mapper, base_config):
        raw = _raw_rule("[global] Some Rule", tags=["global"])
        defaults, _ = mapper.to_domain_split([raw], base_config)
        assert defaults[0].name == "Some Rule"

    def test_non_global_prefix_is_preserved(self, mapper, base_config):
        raw = _raw_rule("[Absence] Errores 500", tags=["api-mngt"])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.name == "[Absence] Errores 500"


class TestExtractApis:
    def test_extracts_apis_from_positive_kql(self, mapper, base_config):
        kql = (
            'alerta500.keyword: "true" AND transactionElement.serviceName: ('
            '"absence" OR "employee-labor-absence" OR "employee-labor-absence-entitlement")'
        )
        raw = _raw_rule("[Absence] Errores 500", tags=["api-mngt"], kql=kql)
        result = mapper.to_domain([raw], base_config)[0]
        assert "absence" in result.apis_alertadas

    def test_does_not_extract_negated_apis_as_targeted_apis(self, mapper, base_config):
        kql = (
            'alerta500.keyword: "true" AND ('
            'NOT transactionElement.serviceName: payroll AND '
            'NOT transactionElement.serviceName: absence AND '
            'NOT transactionElement.serviceName: suppliers)'
        )
        raw = _raw_rule("[Global] Errores 500 por API y método", tags=["api-mngt", "global"], kql=kql)
        defaults, _ = mapper.to_domain_split([raw], base_config)
        assert defaults[0].apis_alertadas == []

    def test_excludes_negated_apis_from_positive_matches(self, mapper, base_config):
        kql = (
            'alerta500.keyword: "true" AND '
            'transactionElement.serviceName: my-api AND '
            'NOT transactionElement.serviceName: other-api'
        )
        raw = _raw_rule("[Team] Errores 500 my-api", tags=["api-mngt"], kql=kql)
        result = mapper.to_domain([raw], base_config)[0]
        assert "my-api" in result.apis_alertadas
        assert "other-api" not in result.apis_alertadas

    def test_esql_rule_has_empty_apis(self, mapper, base_config):
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
        defaults, _ = mapper.to_domain_split([raw], base_config)
        assert defaults[0].apis_alertadas == []


class TestNotificationChannel:
    def test_servicenow_takes_priority_over_teams(self, mapper, base_config):
        """ServiceNow (omi) should win over Microsoft Teams when both are present."""
        actions = [
            {
                "connector_type_id": ".webhook",
                "params": {"body": '[{"labels": {"msteams": "true"}}]'},
            },
            {
                "connector_type_id": ".webhook",
                "params": {"body": '[{"labels": {"omi": "true"}}]'},
            },
        ]
        raw = _raw_rule("Rule with both channels", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "ServiceNow"

    def test_single_teams_channel(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".webhook",
                "params": {"body": '[{"labels": {"msteams": "true"}}]'},
            }
        ]
        raw = _raw_rule("Rule with Teams", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "Microsoft Teams"

    def test_no_channel_returns_none(self, mapper, base_config):
        raw = _raw_rule("Rule without channels", tags=["api-mngt"])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel is None
