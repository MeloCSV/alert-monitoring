import json

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
        assert defaults[0].excluded_apis == ["absence", "payroll", "suppliers"]

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


def _index_action(canal: str, severity: str = None, application: str = None, message: str = None) -> dict:
    doc = {"canal": canal}
    if severity or application or message:
        labels = {}
        if severity:
            labels["severity"] = severity
        if application:
            labels["application"] = application
        annotations = {}
        if message:
            annotations["message"] = message
        doc["alertManagerBody"] = {
            "labels": labels,
            "annotations": annotations,
        }
    return {
        "connector_type_id": ".index",
        "params": {"documents": [doc]},
    }


class TestIndexConnectorChannel:
    def test_canal_alertmanager(self, mapper, base_config):
        raw = _raw_rule("SDDR Alert", tags=[], actions=[_index_action("alertManager")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "AlertManager"

    def test_canal_teams(self, mapper, base_config):
        raw = _raw_rule("FET Alert", tags=[], actions=[_index_action("teams")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "Microsoft Teams"

    def test_canal_omi(self, mapper, base_config):
        raw = _raw_rule("OMI Alert", tags=[], actions=[_index_action("omi")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "ServiceNow"

    def test_canal_itom(self, mapper, base_config):
        raw = _raw_rule("ITOM Alert", tags=[], actions=[_index_action("itom")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "ServiceNow"

    def test_servicenow_beats_teams_across_actions(self, mapper, base_config):
        actions = [_index_action("teams"), _index_action("omi")]
        raw = _raw_rule("Multi channel", tags=[], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "ServiceNow"

    def test_alertmanager_beats_teams(self, mapper, base_config):
        actions = [_index_action("alertManager"), _index_action("teams")]
        raw = _raw_rule("AlertManager+Teams", tags=[], actions=actions)
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel == "AlertManager"

    def test_unknown_canal_returns_none(self, mapper, base_config):
        raw = _raw_rule("Unknown canal", tags=[], actions=[_index_action("unknown_canal")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.notification_channel is None


class TestSeverityFromAlertManagerBody:
    def test_extracts_severity_warning(self, mapper, base_config):
        raw = _raw_rule("SDDR Rule", tags=[], actions=[_index_action("alertManager", severity="warning")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.severity == "Warning"

    def test_extracts_severity_critical(self, mapper, base_config):
        raw = _raw_rule("Critical Rule", tags=[], actions=[_index_action("omi", severity="critical")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.severity == "Critical"

    def test_no_severity_returns_none(self, mapper, base_config):
        raw = _raw_rule("Teams Rule", tags=[], actions=[_index_action("teams")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.severity is None


class TestMessageFromAlertManagerBody:
    def test_extracts_message_from_alertmanagerbody(self, mapper, base_config):
        raw = _raw_rule(
            "SDDR Rule", tags=[],
            actions=[_index_action("alertManager", message="Error en cabecera {{context.hits.0._source.message}}")]
        )
        result = mapper.to_domain([raw], base_config)[0]
        assert result.message == "Error en cabecera {{context.hits.0._source.message}}"

    def test_no_message_returns_none(self, mapper, base_config):
        raw = _raw_rule("Teams Rule", tags=[], actions=[_index_action("teams")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.message is None


class TestApplicationExtraction:
    def test_from_alertmanagerbody_labels(self, mapper, base_config):
        raw = _raw_rule("SDDR Rule", tags=[], actions=[_index_action("alertManager", application="sddr")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.application == "sddr"

    def test_template_value_is_skipped(self, mapper, base_config):
        action = _index_action("alertManager", application="{{context.sourceFields.application}}")
        raw = _raw_rule("Infra Rule", tags=[], actions=[action])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.application is None

    def test_from_kql_application_field(self, mapper, base_config):
        kql = 'application : "fichaje-back-obx-payroll-concept-input" and message : "Failed"'
        raw = _raw_rule("Fichaje Rule", tags=[], kql=kql, actions=[_index_action("teams")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.application == "fichaje-back-obx-payroll-concept-input"

    def test_from_kql_namespace(self, mapper, base_config):
        kql = 'k8s.namespace.name : "sddr-back" and level : "ERROR"'
        raw = _raw_rule("SDDR Namespace Rule", tags=[], kql=kql, actions=[_index_action("teams")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.application == "sddr-back"

    def test_from_esquery_must_namespace(self, mapper, base_config):
        es_query = json.dumps({
            "query": {
                "bool": {
                    "must": [
                        {"term": {"level": {"value": "ERROR"}}},
                        {"term": {"k8s.namespace.name": {"value": "fet-back"}}},
                    ]
                }
            }
        })
        raw = {
            "id": "esq-1", "enabled": True, "name": "FET Rule", "tags": [],
            "schedule": {"interval": "3m"},
            "actions": [_index_action("teams")],
            "params": {"searchType": "esQuery", "esQuery": es_query, "index": ["logs-otel-fet-*"]},
        }
        result = mapper.to_domain([raw], base_config)[0]
        assert result.application == "fet-back"

    def test_from_index_pattern_fallback(self, mapper, base_config):
        raw = {
            "id": "idx-1", "enabled": True, "name": "Index Rule", "tags": [],
            "schedule": {"interval": "3m"},
            "actions": [_index_action("teams")],
            "params": {"searchType": "esQuery", "esQuery": '{"query": {}}', "index": ["logs-otel-sddr-gke-pro*"]},
        }
        result = mapper.to_domain([raw], base_config)[0]
        assert result.application == "sddr"

    def test_no_application_returns_none(self, mapper, base_config):
        raw = _raw_rule("Generic Rule", tags=[], actions=[_index_action("teams")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.application is None


class TestMicroserviceExtraction:
    def test_from_kql_deployment(self, mapper, base_config):
        kql = 'message: "error" and k8s.deployment.name:"sddr-back-web-statusevent"'
        raw = _raw_rule("SDDR Deploy Rule", tags=[], kql=kql, actions=[_index_action("alertManager")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.microservice == "sddr-back-web-statusevent"

    def test_negated_deployment_is_ignored(self, mapper, base_config):
        kql = 'level: "ERROR" AND NOT k8s.deployment.name:"excluded-svc"'
        raw = _raw_rule("FET Rule", tags=[], kql=kql, actions=[_index_action("teams")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.microservice is None

    def test_from_esquery_must_deployment(self, mapper, base_config):
        es_query = json.dumps({
            "query": {
                "bool": {
                    "must": [
                        {"match": {"k8s.deployment.name": "sddr-back-web-manage-transaction"}},
                    ]
                }
            }
        })
        raw = {
            "id": "esq-2", "enabled": True, "name": "Deploy Rule", "tags": [],
            "schedule": {"interval": "1m"},
            "actions": [_index_action("alertManager")],
            "params": {"searchType": "esQuery", "esQuery": es_query, "index": ["logs-otel-sddr-gke-pro*"]},
        }
        result = mapper.to_domain([raw], base_config)[0]
        assert result.microservice == "sddr-back-web-manage-transaction"

    def test_no_deployment_returns_none(self, mapper, base_config):
        raw = _raw_rule("Generic Rule", tags=[], actions=[_index_action("teams")])
        result = mapper.to_domain([raw], base_config)[0]
        assert result.microservice is None
