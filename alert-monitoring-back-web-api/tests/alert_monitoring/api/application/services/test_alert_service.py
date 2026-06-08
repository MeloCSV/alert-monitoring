import pytest

from alert_monitoring.api.application.services.alert_service import AlertService
from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher


def _make_blackout(matchers: list[BlackoutMatcher]) -> Blackout:
    return Blackout(id='test-id', matchers=matchers)


def _matcher(name: str, value: str, is_regex: bool = False, is_equal: bool = True) -> BlackoutMatcher:
    return BlackoutMatcher(name=name, value=value, is_regex=is_regex, is_equal=is_equal)


class TestBlackoutMatchesSolution:
    """Unit tests for AlertService._blackout_matches_solution (pure logic, no DI needed)."""

    @pytest.fixture
    def match(self):
        return AlertService._blackout_matches_solution

    def test_exact_namespace_match(self, match):
        """
        Given blackout with namespace=my-app
        When solution is my-app
        Then should match
        """
        b = _make_blackout([_matcher('namespace', 'my-app')])
        assert match(None, b, 'my-app') is True

    def test_back_variant_matches(self, match):
        """
        Given blackout with namespace=my-app-back
        When solution is my-app
        Then should match (backend variant)
        """
        b = _make_blackout([_matcher('namespace', 'my-app-back')])
        assert match(None, b, 'my-app') is True

    def test_front_variant_matches(self, match):
        """
        Given blackout with namespace=my-app-front
        When solution is my-app
        Then should match (frontend variant)
        """
        b = _make_blackout([_matcher('namespace', 'my-app-front')])
        assert match(None, b, 'my-app') is True

    def test_unrelated_namespace_does_not_match(self, match):
        """
        Given blackout with different namespace
        When solution is my-app
        Then should not match
        """
        b = _make_blackout([_matcher('namespace', 'other-app')])
        assert match(None, b, 'my-app') is False

    def test_regex_matcher_matches_solution(self, match):
        """
        Given blackout with regex matcher matching the solution
        When solution is my-app
        Then should match
        """
        b = _make_blackout([_matcher('namespace', 'my-app.*', is_regex=True)])
        assert match(None, b, 'my-app') is True

    def test_regex_matcher_matches_back_variant(self, match):
        """
        Given regex matching all my-app variants
        When solution is my-app
        Then should match via back variant
        """
        b = _make_blackout([_matcher('namespace', 'my-app-.*', is_regex=True)])
        assert match(None, b, 'my-app') is True

    def test_non_matching_field_name_is_ignored(self, match):
        """
        Given blackout with alertname field (not a namespace-like field)
        When solution is my-app
        Then should not match
        """
        b = _make_blackout([_matcher('alertname', 'my-app')])
        assert match(None, b, 'my-app') is False

    def test_is_equal_false_is_ignored(self, match):
        """
        Given blackout with is_equal=False (exclusion matcher)
        When solution is my-app
        Then should not match (negation matchers are skipped)
        """
        b = _make_blackout([_matcher('namespace', 'my-app', is_equal=False)])
        assert match(None, b, 'my-app') is False

    def test_deployment_field_matches(self, match):
        """
        Given blackout with deployment=my-app-back
        When solution is my-app
        Then should match
        """
        b = _make_blackout([_matcher('deployment', 'my-app-back')])
        assert match(None, b, 'my-app') is True

    def test_solucion_field_matches(self, match):
        """
        Given blackout with solucion field (Spanish label used by Prometheus)
        When solution is my-app
        Then should match
        """
        b = _make_blackout([_matcher('solucion', 'my-app')])
        assert match(None, b, 'my-app') is True

    def test_case_insensitive_match(self, match):
        """
        Given blackout with uppercase namespace value
        When solution is lowercase
        Then should match case-insensitively
        """
        b = _make_blackout([_matcher('namespace', 'MY-APP')])
        assert match(None, b, 'my-app') is True

    def test_prefix_child_namespace_matches(self, match):
        """
        Given blackout with namespace=my-app-worker (starts with solution-)
        When solution is my-app
        Then should match
        """
        b = _make_blackout([_matcher('namespace', 'my-app-worker')])
        assert match(None, b, 'my-app') is True
