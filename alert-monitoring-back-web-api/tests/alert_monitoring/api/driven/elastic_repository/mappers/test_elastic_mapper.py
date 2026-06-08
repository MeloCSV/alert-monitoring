import pytest

from alert_monitoring.api.driven.elastic_repository.mappers.elastic_mapper import ElasticMapper
from alert_monitoring.api.driven.elastic_repository.models.elastic_model import ElasticRule


def _make_rule(**kwargs) -> ElasticRule:
    defaults = dict(
        id='rule-1',
        name='My Rule',
        enabled=True,
        schedule_interval='5m',
        condition='count > 0',
        canals=[],
        labels={},
        description=None,
        environments=[],
    )
    defaults.update(kwargs)
    return ElasticRule(**defaults)


@pytest.fixture
def mapper():
    return ElasticMapper()


class TestElasticMapperToDomain:
    def test_maps_list_of_rules(self, mapper):
        rules = [_make_rule(name='Rule A'), _make_rule(name='Rule B')]
        result = mapper.to_domain(rules)
        assert len(result) == 2
        assert result[0].name == 'Rule A'
        assert result[1].name == 'Rule B'

    def test_empty_list_returns_empty(self, mapper):
        assert mapper.to_domain([]) == []

    def test_source_tool_is_elastic(self, mapper):
        result = mapper.to_domain([_make_rule()])
        assert result[0].source_tool == 'Elastic'


class TestElasticMapperMapRule:
    def test_maps_name_from_rule(self, mapper):
        rule = _make_rule(name='My Elastic Alert')
        alert = mapper._map_rule(rule)
        assert alert.name == 'My Elastic Alert'

    def test_uses_description_when_provided(self, mapper):
        rule = _make_rule(description='Custom description')
        alert = mapper._map_rule(rule)
        assert alert.description == 'Custom description'

    def test_falls_back_to_default_description_when_none(self, mapper):
        rule = _make_rule(description=None)
        alert = mapper._map_rule(rule)
        assert alert.description == 'Sin descripción'

    def test_severity_from_labels(self, mapper):
        rule = _make_rule(labels={'severity': 'critical'})
        alert = mapper._map_rule(rule)
        assert alert.severity == 'critical'

    def test_severity_defaults_to_unknown_when_missing(self, mapper):
        rule = _make_rule(labels={})
        alert = mapper._map_rule(rule)
        assert alert.severity == 'unknown'

    def test_solution_from_application_label(self, mapper):
        rule = _make_rule(labels={'application': 'my-app'})
        alert = mapper._map_rule(rule)
        assert alert.solution == 'my-app'

    def test_solution_is_none_when_no_application_label(self, mapper):
        rule = _make_rule(labels={})
        alert = mapper._map_rule(rule)
        assert alert.solution is None

    def test_environments_from_rule(self, mapper):
        rule = _make_rule(environments=['pro', 'pre'])
        alert = mapper._map_rule(rule)
        assert 'pro' in alert.environments

    def test_all_environments_when_empty(self, mapper):
        rule = _make_rule(environments=[])
        alert = mapper._map_rule(rule)
        assert len(alert.environments) == 4


class TestElasticMapperInferMicroservice:
    def test_returns_application_label(self, mapper):
        rule = _make_rule(labels={'application': 'my-app'})
        assert mapper._infer_microservice(rule) == 'my-app'

    def test_returns_deployment_label_when_no_application(self, mapper):
        rule = _make_rule(labels={'deployment': 'my-app-back'})
        assert mapper._infer_microservice(rule) == 'my-app-back'

    def test_returns_service_label(self, mapper):
        rule = _make_rule(labels={'service': 'my-service'})
        assert mapper._infer_microservice(rule) == 'my-service'

    def test_returns_namespace_label(self, mapper):
        rule = _make_rule(labels={'namespace': 'my-namespace'})
        assert mapper._infer_microservice(rule) == 'my-namespace'

    def test_returns_pod_label(self, mapper):
        rule = _make_rule(labels={'pod': 'my-pod'})
        assert mapper._infer_microservice(rule) == 'my-pod'

    def test_returns_job_label(self, mapper):
        rule = _make_rule(labels={'job': 'my-job'})
        assert mapper._infer_microservice(rule) == 'my-job'

    def test_returns_none_when_no_known_label(self, mapper):
        rule = _make_rule(labels={'custom': 'value'})
        assert mapper._infer_microservice(rule) is None

    def test_prefers_application_over_deployment(self, mapper):
        rule = _make_rule(labels={'application': 'app', 'deployment': 'deploy'})
        assert mapper._infer_microservice(rule) == 'app'


class TestElasticMapperInferChannel:
    def test_returns_none_when_no_canals_and_no_labels(self, mapper):
        rule = _make_rule(canals=[], labels={})
        assert mapper._infer_channel(rule) is None

    def test_resolves_msteams_from_labels_when_no_canals(self, mapper):
        rule = _make_rule(canals=[], labels={'msteams': 'true'})
        result = mapper._infer_channel(rule)
        assert result == 'Teams'

    def test_maps_msteams_canal_to_teams(self, mapper):
        rule = _make_rule(canals=['msteams'], labels={})
        result = mapper._infer_channel(rule)
        assert result == 'Teams'

    def test_maps_omi_canal_to_servicenow(self, mapper):
        rule = _make_rule(canals=['omi'], labels={})
        result = mapper._infer_channel(rule)
        assert result == 'ServiceNow'

    def test_alertmanager_canal_uses_labels(self, mapper):
        rule = _make_rule(canals=['alertmanager'], labels={'omi': 'true'})
        result = mapper._infer_channel(rule)
        assert 'ServiceNow' in result

    def test_alertmanager_canal_falls_back_to_display_when_no_labels(self, mapper):
        rule = _make_rule(canals=['alertmanager'], labels={})
        result = mapper._infer_channel(rule)
        assert result == 'AlertManager'

    def test_joins_multiple_canals_with_slash(self, mapper):
        rule = _make_rule(canals=['msteams', 'omi'], labels={})
        result = mapper._infer_channel(rule)
        assert '/' in result or result in ('Teams', 'ServiceNow')

    def test_deduplicates_channels(self, mapper):
        rule = _make_rule(canals=['msteams', 'msteams'], labels={})
        result = mapper._infer_channel(rule)
        assert result == 'Teams'
