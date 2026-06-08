import pytest

from alert_monitoring.api.driven.prometheus_repository.mappers.prometheus_mapper import (
    PrometheusMapper,
    is_default_rule,
)
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule


def _rule(alert='MyAlert', expr='', labels=None, annotations=None, group_name='my-app.rules', cluster_name='') -> PrometheusRule:
    return PrometheusRule(
        alert=alert,
        expr=expr,
        labels=labels or {},
        annotations=annotations or {},
        group_name=group_name,
        cluster_name=cluster_name,
    )


def _default_rule(alert='Default_Status', expr='', extra_labels=None) -> PrometheusRule:
    labels = {'alertype': 'default', 'severity': 'warning'}
    if extra_labels:
        labels.update(extra_labels)
    return PrometheusRule(
        alert=alert,
        expr=expr,
        labels=labels,
        annotations={},
        group_name='default.rules',
        cluster_name='',
    )


@pytest.fixture
def mapper():
    return PrometheusMapper()


# ---------------------------------------------------------------------------
# is_default_rule
# ---------------------------------------------------------------------------

class TestIsDefaultRule:
    def test_true_when_alertype_default_and_group_starts_with_default(self):
        rule = _default_rule()
        assert is_default_rule(rule) is True

    def test_false_when_alertype_missing(self):
        rule = _rule(group_name='default.rules')
        assert is_default_rule(rule) is False

    def test_false_when_group_name_does_not_start_with_default(self):
        rule = _rule(labels={'alertype': 'default'}, group_name='my-app.rules')
        assert is_default_rule(rule) is False

    def test_case_insensitive_alertype(self):
        rule = PrometheusRule(
            alert='X', expr='', labels={'alertype': 'DEFAULT'},
            annotations={}, group_name='default.rules', cluster_name='',
        )
        assert is_default_rule(rule) is True


# ---------------------------------------------------------------------------
# PrometheusMapper.to_domain
# ---------------------------------------------------------------------------

class TestPrometheusMapperToDomain:
    def test_maps_single_rule(self, mapper):
        rule = _rule()
        result = mapper.to_domain([rule])
        assert len(result) == 1

    def test_alert_type_adhoc_for_non_default(self, mapper):
        rule = _rule()
        result = mapper.to_domain([rule])
        assert result[0].alert_type == 'Ad-hoc'

    def test_alert_type_por_defecto_for_default(self, mapper):
        rule = _default_rule()
        result = mapper.to_domain([rule])
        assert result[0].alert_type == 'Por Defecto'

    def test_name_is_raw_name_for_default_rule(self, mapper):
        rule = _default_rule(alert='Default_Status some label')
        result = mapper.to_domain([rule])
        assert result[0].name == 'Default_Status'

    def test_name_is_full_alert_for_adhoc(self, mapper):
        rule = _rule(alert='Full Alert Name')
        result = mapper.to_domain([rule])
        assert result[0].name == 'Full Alert Name'

    def test_description_from_annotations(self, mapper):
        rule = _rule(annotations={'message': 'Alert fired!'})
        result = mapper.to_domain([rule])
        assert result[0].description == 'Alert fired!'

    def test_default_description_when_no_message(self, mapper):
        rule = _rule(annotations={})
        result = mapper.to_domain([rule])
        assert result[0].description == 'Sin descripción'

    def test_severity_from_labels(self, mapper):
        rule = _rule(labels={'severity': 'critical'})
        result = mapper.to_domain([rule])
        assert result[0].severity == 'critical'

    def test_severity_defaults_to_unknown(self, mapper):
        rule = _rule(labels={})
        result = mapper.to_domain([rule])
        assert result[0].severity == 'unknown'

    def test_source_tool_is_prometheus(self, mapper):
        rule = _rule()
        result = mapper.to_domain([rule])
        assert result[0].source_tool == 'Prometheus'

    def test_cluster_from_rule(self, mapper):
        rule = _rule(cluster_name='my-cluster')
        result = mapper.to_domain([rule])
        assert result[0].cluster == 'my-cluster'

    def test_cluster_none_when_empty(self, mapper):
        rule = _rule(cluster_name='')
        result = mapper.to_domain([rule])
        assert result[0].cluster is None

    def test_prometheus_name_set_for_default(self, mapper):
        rule = _default_rule(alert='Default_Status raw')
        result = mapper.to_domain([rule])
        assert result[0].prometheus_name == 'Default_Status'

    def test_prometheus_name_none_for_adhoc(self, mapper):
        rule = _rule()
        result = mapper.to_domain([rule])
        assert result[0].prometheus_name is None

    def test_environments_are_pro_for_default(self, mapper):
        rule = _default_rule()
        result = mapper.to_domain([rule])
        assert result[0].environments == ['pro']

    def test_chips_empty_for_default(self, mapper):
        rule = _default_rule(expr='deployment=~"app-back"')
        result = mapper.to_domain([rule])
        assert result[0].chips == []


# ---------------------------------------------------------------------------
# _infer_solution
# ---------------------------------------------------------------------------

class TestInferSolution:
    def test_uses_solucion_label(self, mapper):
        rule = _rule(labels={'solucion': 'my-solution'})
        result = mapper.to_domain([rule])
        assert result[0].solution == 'my-solution'

    def test_falls_back_to_group_name(self, mapper):
        rule = _rule(group_name='my-app.rules')
        result = mapper.to_domain([rule])
        assert result[0].solution == 'my-app'

    def test_strips_criticas_suffix(self, mapper):
        rule = _rule(group_name='my-app-críticas')
        result = mapper.to_domain([rule])
        assert result[0].solution == 'my-app'

    def test_unknown_when_no_group_name(self, mapper):
        rule = PrometheusRule(alert='X', expr='', labels={}, annotations={}, group_name='', cluster_name='')
        result = mapper.to_domain([rule])
        assert result[0].solution == 'unknown'


# ---------------------------------------------------------------------------
# _infer_channel
# ---------------------------------------------------------------------------

class TestInferChannel:
    def test_canal_label_wins(self, mapper):
        rule = _rule(labels={'canal': 'omi'})
        result = mapper.to_domain([rule])
        assert result[0].notification_channel == 'ServiceNow'

    def test_bool_label_msteams(self, mapper):
        rule = _rule(labels={'msteams': 'true'})
        result = mapper.to_domain([rule])
        assert result[0].notification_channel == 'Teams'

    def test_no_channel_returns_none(self, mapper):
        rule = _rule(labels={})
        result = mapper.to_domain([rule])
        assert result[0].notification_channel is None


# ---------------------------------------------------------------------------
# _infer_microservice
# ---------------------------------------------------------------------------

class TestInferMicroservice:
    def test_uses_service_label(self, mapper):
        rule = _rule(labels={'service': 'my-service'})
        result = mapper.to_domain([rule])
        assert result[0].microservice == 'my-service'

    def test_uses_namespace_label_when_no_service(self, mapper):
        rule = _rule(labels={'namespace': 'my-ns'})
        result = mapper.to_domain([rule])
        assert result[0].microservice == 'my-ns'

    def test_extracts_namespace_from_expr(self, mapper):
        rule = _rule(expr='rate(http_requests{namespace="my-app"}[5m])')
        result = mapper.to_domain([rule])
        assert result[0].microservice == 'my-app'

    def test_falls_back_to_group_name(self, mapper):
        rule = PrometheusRule(alert='X', expr='', labels={}, annotations={}, group_name='my-svc.rules', cluster_name='')
        result = mapper.to_domain([rule])
        assert result[0].microservice == 'my-svc'


# ---------------------------------------------------------------------------
# _infer_environments
# ---------------------------------------------------------------------------

class TestInferEnvironments:
    def test_uses_environment_label(self, mapper):
        rule = _rule(labels={'environment': 'pre'})
        result = mapper.to_domain([rule])
        assert 'pre' in result[0].environments

    def test_uses_env_label(self, mapper):
        rule = _rule(labels={'env': 'dev'})
        result = mapper.to_domain([rule])
        assert 'dev' in result[0].environments

    def test_extracts_from_expr(self, mapper):
        rule = _rule(expr='metric{environment=~"dev|pre"}')
        result = mapper.to_domain([rule])
        assert 'dev' in result[0].environments
        assert 'pre' in result[0].environments

    def test_defaults_to_all_when_no_env(self, mapper):
        rule = _rule(labels={}, expr='metric{severity="critical"}')
        result = mapper.to_domain([rule])
        assert result[0].environments == ['dev', 'itg', 'pre', 'pro']

    def test_ignores_template_placeholders(self, mapper):
        rule = _rule(labels={'environment': '{{ $labels.env }}'})
        result = mapper.to_domain([rule])
        assert result[0].environments == ['dev', 'itg', 'pre', 'pro']
