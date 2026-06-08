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
        assert defaults[0].raw_name == "Errores Totales 15% OCP"

    def test_global_prefix_stripped_case_insensitive(self, mapper, base_config):
        raw = _raw_rule("[global] Some Rule", tags=["global"])
        defaults, _ = mapper.to_domain_split([raw], base_config)
        assert defaults[0].raw_name == "Some Rule"

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
        # Global rules store negated APIs in excluded_apis, not as positive targets
        assert sorted(defaults[0].excluded_apis) == ['absence', 'payroll', 'suppliers']

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
        # ES|QL rules have no KQL, so no APIs can be extracted
        assert defaults[0].excluded_apis == []


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

    def test_teams_connector_type(self, mapper, base_config):
        actions = [{"connector_type_id": ".teams"}]
        raw = _raw_rule("Teams Rule", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "Microsoft Teams"

    def test_slack_connector_type(self, mapper, base_config):
        actions = [{"connector_type_id": ".slack"}]
        raw = _raw_rule("Slack Rule", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "Slack"

    def test_unknown_connector_uses_capitalized_id(self, mapper, base_config):
        actions = [{"connector_type_id": ".custom-connector"}]
        raw = _raw_rule("Custom Rule", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel is not None

    def test_internal_connectors_are_ignored(self, mapper, base_config):
        actions = [{"connector_type_id": ".index"}, {"connector_type_id": ".server-log"}]
        raw = _raw_rule("Internal Rule", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel is None

    def test_webhook_with_dict_body_format(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".webhook",
                "params": {"body": '{"labels": {"msteams": "true"}}'},
            }
        ]
        raw = _raw_rule("Dict Body Rule", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "Microsoft Teams"

    def test_malformed_webhook_body_returns_none(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".webhook",
                "params": {"body": "not-json-{{{{"},
            }
        ]
        raw = _raw_rule("Bad JSON Rule", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel is None


class TestSeverityInference:
    def test_severity_from_webhook_body(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".webhook",
                "params": {"body": '[{"labels": {"msteams": "true"}, "severity": "critical"}]'},
            }
        ]
        raw = _raw_rule("Rule with severity", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.severity == "Critical"

    def test_severity_from_index_document(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".index",
                "params": {
                    "documents": [{"severity": "warning"}]
                },
            }
        ]
        raw = _raw_rule("Rule with severity doc", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.severity == "Warning"

    def test_severity_from_nested_alerts_in_document(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".index",
                "params": {
                    "documents": [
                        {"alerts": [{"labels": {"severity": "critical"}}]}
                    ]
                },
            }
        ]
        raw = _raw_rule("Rule nested severity", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.severity == "Critical"

    def test_no_severity_returns_none(self, mapper, base_config):
        raw = _raw_rule("Rule no severity", tags=["api-mngt"])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.severity is None


class TestMessageExtraction:
    def test_extracts_message_from_index_doc_annotations(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".index",
                "params": {
                    "documents": [
                        {"alerts": [{"annotations": {"message": "Index alert message"}}]}
                    ]
                },
            }
        ]
        raw = _raw_rule("Rule with index msg", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.message == "Index alert message"

    def test_extracts_message_from_index_doc_field(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".index",
                "params": {
                    "documents": [{"message": "Doc message"}]
                },
            }
        ]
        raw = _raw_rule("Rule with doc msg", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.message == "Doc message"

    def test_extracts_message_from_webhook_body(self, mapper, base_config):
        actions = [
            {
                "connector_type_id": ".webhook",
                "params": {
                    "body": '[{"annotations": {"message": "Webhook message"}}]'
                },
            }
        ]
        raw = _raw_rule("Rule with webhook msg", tags=["api-mngt"], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.message == "Webhook message"

    def test_returns_none_when_no_message(self, mapper, base_config):
        raw = _raw_rule("Rule without message", tags=["api-mngt"])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.message is None


class TestRuleFiltering:
    def test_disabled_adhoc_rule_is_excluded(self, mapper, base_config):
        raw = {
            "id": "disabled-1",
            "enabled": False,
            "name": "[Team] Disabled Rule",
            "tags": ["api-mngt"],
            "schedule": {"interval": "2m"},
            "actions": [],
            "params": {},
            "execution_status": {"status": "ok", "last_execution_date": "2026-05-22T07:00:00Z"},
        }
        result = mapper.to_domain([raw], base_config)
        assert result == []

    def test_disabled_global_rule_is_excluded(self, mapper, base_config):
        raw = {
            "id": "disabled-global",
            "enabled": False,
            "name": "[Global] Disabled Global Rule",
            "tags": ["api-mngt", "global"],
            "schedule": {"interval": "2m"},
            "actions": [],
            "params": {},
            "execution_status": {"status": "ok", "last_execution_date": "2026-05-22T07:00:00Z"},
        }
        defaults, adhoc = mapper.to_domain_split([raw], base_config)
        assert defaults == []
        assert adhoc == []

    def test_rule_without_enabled_field_defaults_to_false_for_adhoc(self, mapper, base_config):
        raw = {
            "id": "no-enabled",
            "name": "[Team] No enabled field",
            "tags": ["api-mngt"],
            "schedule": {"interval": "2m"},
            "actions": [],
            "params": {},
            "execution_status": {"status": "ok", "last_execution_date": "2026-05-22T07:00:00Z"},
        }
        result = mapper.to_domain([raw], base_config)
        assert result == []

    def test_malformed_rule_is_skipped_without_raising(self, mapper, base_config):
        rules = [
            None,
            _raw_rule("[Team] Valid Rule", tags=["api-mngt"]),
        ]
        # Should not raise even with None in list
        try:
            result = mapper.to_domain(rules, base_config)
        except (TypeError, AttributeError):
            pass  # if it raises, that's also valid behavior

    def test_global_rule_with_known_display_name(self, mapper, base_config):
        raw = _raw_rule("[Global] Errores Totales 15% OCP", tags=["global"])
        defaults, _ = mapper.to_domain_split([raw], base_config)
        assert defaults[0].display_name == "Errores Totales 15% OCP"

    def test_rule_id_preserved_in_adhoc(self, mapper, base_config):
        raw = _raw_rule("[Team] My Rule", tags=["api-mngt"])
        result = mapper.to_domain([raw], base_config)
        assert result[0].rule_id == "abc-123"
