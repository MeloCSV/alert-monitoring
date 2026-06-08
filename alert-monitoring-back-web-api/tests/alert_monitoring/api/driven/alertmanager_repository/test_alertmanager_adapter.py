import pytest
from unittest.mock import MagicMock

from alert_monitoring.api.driven.alertmanager_repository.adapters.alertmanager_adapter import AlertManagerAdapter
from alert_monitoring.api.driven.alertmanager_repository.models.alertmanager_config import AlertManagerConfig


def _make_config(name='test-am', url='http://am.example.com'):
    return AlertManagerConfig(name=name, url=url)


def _raw_silence(id='s1', state='active', matchers=None, starts_at=None, ends_at=None):
    return {
        'id': id,
        'status': {'state': state},
        'matchers': matchers if matchers is not None else [{'name': 'namespace', 'value': 'my-app', 'isRegex': False, 'isEqual': True}],
        'startsAt': starts_at or '2025-01-01T00:00:00Z',
        'endsAt': ends_at or '2025-12-31T23:59:59Z',
        'createdBy': 'admin',
        'comment': 'test silence',
    }


class TestAlertManagerAdapterFetchActiveBlackouts:
    def test_returns_empty_when_no_configs(self):
        client = MagicMock()
        adapter = AlertManagerAdapter(client=client)
        result = adapter.fetch_active_blackouts(configs=[])
        assert result == []
        client.fetch_silences.assert_not_called()

    def test_returns_active_blackouts(self):
        client = MagicMock()
        client.fetch_silences.return_value = [_raw_silence(state='active')]
        adapter = AlertManagerAdapter(client=client)

        result = adapter.fetch_active_blackouts(configs=[_make_config()])

        assert len(result) == 1
        assert result[0].id == 's1'
        assert result[0].state == 'active'

    def test_filters_out_expired_silences(self):
        client = MagicMock()
        client.fetch_silences.return_value = [
            _raw_silence(id='active', state='active'),
            _raw_silence(id='expired', state='expired'),
        ]
        adapter = AlertManagerAdapter(client=client)

        result = adapter.fetch_active_blackouts(configs=[_make_config()])

        assert len(result) == 1
        assert result[0].id == 'active'

    def test_maps_matchers_correctly(self):
        client = MagicMock()
        client.fetch_silences.return_value = [_raw_silence(matchers=[
            {'name': 'namespace', 'value': 'my-app', 'isRegex': False, 'isEqual': True}
        ])]
        adapter = AlertManagerAdapter(client=client)

        result = adapter.fetch_active_blackouts(configs=[_make_config()])

        matcher = result[0].matchers[0]
        assert matcher.name == 'namespace'
        assert matcher.value == 'my-app'
        assert matcher.is_regex is False
        assert matcher.is_equal is True

    def test_aggregates_from_multiple_configs(self):
        client = MagicMock()
        client.fetch_silences.side_effect = [
            [_raw_silence(id='s1')],
            [_raw_silence(id='s2')],
        ]
        adapter = AlertManagerAdapter(client=client)

        result = adapter.fetch_active_blackouts(configs=[_make_config('am1'), _make_config('am2')])

        assert len(result) == 2

    def test_malformed_silence_is_skipped(self):
        client = MagicMock()
        client.fetch_silences.return_value = [None]
        adapter = AlertManagerAdapter(client=client)

        result = adapter.fetch_active_blackouts(configs=[_make_config()])

        assert result == []

    def test_silence_with_no_matchers(self):
        client = MagicMock()
        client.fetch_silences.return_value = [_raw_silence(matchers=[])]
        adapter = AlertManagerAdapter(client=client)

        result = adapter.fetch_active_blackouts(configs=[_make_config()])

        assert len(result) == 1
        assert result[0].matchers == []


class TestAlertManagerAdapterToDomain:
    @pytest.fixture
    def adapter(self):
        return AlertManagerAdapter(client=MagicMock())

    def test_maps_all_fields(self, adapter):
        raw = _raw_silence()
        result = adapter._to_domain(raw, source='test-am')
        assert result.id == 's1'
        assert result.state == 'active'
        assert result.created_by == 'admin'
        assert result.comment == 'test silence'
        assert result.source == 'test-am'

    def test_returns_none_for_malformed_data(self, adapter):
        result = adapter._to_domain(None)
        assert result is None

    def test_empty_matchers_list(self, adapter):
        raw = _raw_silence(matchers=[])
        result = adapter._to_domain(raw)
        assert result.matchers == []

    def test_state_defaults_to_active_when_missing(self, adapter):
        raw = {'id': 's1', 'status': {}, 'matchers': []}
        result = adapter._to_domain(raw)
        assert result.state == 'active'
