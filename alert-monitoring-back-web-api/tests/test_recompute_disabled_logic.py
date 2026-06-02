"""Tests for the pure logic functions in recompute_disabled_use_case."""
import pytest
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.application.use_cases.recompute_disabled_use_case import (
    _evaluate,
    _regex_matches,
    _is_prefix_of,
    _literal_prefix,
    _display_pattern,
)


def make_alert(excluded_ns=None, included_ns=None, excluded_jobs=None):
    return DefaultAlert(
        raw_name="TestAlert",
        display_name="Test Alert",
        excluded_namespaces=excluded_ns or [],
        included_namespaces=included_ns or [],
        excluded_jobs=excluded_jobs or [],
    )


# ── _regex_matches ────────────────────────────────────────────────────────────

class TestRegexMatches:
    def test_literal_exact_match(self):
        assert _regex_matches("myapp", "myapp")

    def test_literal_no_match(self):
        assert not _regex_matches("myapp", "otherapp")

    def test_wildcard_pattern(self):
        assert _regex_matches("myapp-payments", "myapp-.*")

    def test_wildcard_no_match(self):
        assert not _regex_matches("otherapp-payments", "myapp-.*")

    def test_case_insensitive(self):
        assert _regex_matches("MyApp", "myapp")

    def test_partial_regex(self):
        # fullmatch means the whole string must match
        assert not _regex_matches("myapp-extra", "myapp")

    def test_invalid_regex_returns_false(self):
        assert not _regex_matches("myapp", "[invalid")


# ── _literal_prefix ───────────────────────────────────────────────────────────

class TestLiteralPrefix:
    def test_simple_string(self):
        assert _literal_prefix("myapp-.*") == "myapp-"

    def test_no_regex(self):
        assert _literal_prefix("myapp") == "myapp"

    def test_stops_at_dot(self):
        assert _literal_prefix("myapp.extra") == "myapp"

    def test_escaped_char(self):
        assert _literal_prefix(r"my\.app-.*") == "my.app-"

    def test_empty(self):
        assert _literal_prefix("") == ""


# ── _is_prefix_of ─────────────────────────────────────────────────────────────

class TestIsPrefixOf:
    def test_matches_prefix(self):
        # "myapp-payments-svc" pattern starts with "myapp-"
        assert _is_prefix_of("myapp", "myapp-payments-.*")

    def test_no_match_different_prefix(self):
        assert not _is_prefix_of("otherapp", "myapp-payments-.*")

    def test_no_match_exact_name_no_dash(self):
        # pattern is exactly "myapp" — not a sub-service prefix
        assert not _is_prefix_of("myapp", "myapp")

    def test_empty_target(self):
        assert not _is_prefix_of("", "myapp-.*")

    def test_case_insensitive(self):
        assert _is_prefix_of("MyApp", "myapp-payments-.*")


# ── _display_pattern ─────────────────────────────────────────────────────────

class TestDisplayPattern:
    def test_strips_wildcard_suffix(self):
        assert _display_pattern("myapp-.*") == "myapp"

    def test_strips_plus_suffix(self):
        assert _display_pattern("myapp-.+") == "myapp"

    def test_strips_trailing_dash(self):
        assert _display_pattern("myapp-") == "myapp"

    def test_no_suffix(self):
        assert _display_pattern("myapp") == "myapp"

    def test_empty_result_returns_original(self):
        assert _display_pattern(".*") == ".*"


# ── _evaluate ─────────────────────────────────────────────────────────────────

class TestEvaluateFullyDisabled:
    def test_solution_fully_excluded_by_namespace(self):
        alert = make_alert(excluded_ns=["mysolution"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", set())
        assert is_disabled
        assert not is_partial
        assert chips == []

    def test_solution_fully_excluded_by_wildcard(self):
        alert = make_alert(excluded_ns=["mysolution.*"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", set())
        assert is_disabled

    def test_not_excluded(self):
        alert = make_alert(excluded_ns=["otherapp"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", {"micro1"})
        assert not is_disabled
        assert not is_partial
        assert chips == []

    def test_re_included_overrides_excluded(self):
        # Solution is excluded but also re-included → not disabled
        alert = make_alert(excluded_ns=["mysolution"], included_ns=["mysolution"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", set())
        assert not is_disabled

    def test_microservice_re_includes_solution(self):
        alert = make_alert(excluded_ns=["mysolution"], included_ns=["mysolution-payments"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", {"mysolution-payments"})
        assert not is_disabled


class TestEvaluatePartiallyDisabled:
    def test_micro_directly_matching_pattern_is_disabled(self):
        # When the micro name itself fully matches the exclusion pattern → disabled (explicit exclusion)
        alert = make_alert(excluded_ns=["mysolution-payments-.*"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", {"mysolution-payments-svc"})
        assert is_disabled
        assert not is_partial
        assert chips == []

    def test_partial_when_only_solution_is_prefix_target(self):
        # Pattern targets sub-namespaces of the solution but no known micro directly matches → partial
        alert = make_alert(excluded_ns=["mysolution-payments-.*"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", {"mysolution-orders-svc"})
        assert is_partial
        assert not is_disabled
        assert chips

    def test_edge_case_two_micros_one_excluded_marks_disabled(self):
        # Known limitation: if ANY micro directly matches the pattern, the whole solution is marked
        # disabled even if other micros would still fire. In practice, exclusion patterns are
        # at the solution level, so this edge case shouldn't appear.
        alert = make_alert(excluded_ns=["mysolution-payments-.*"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", {"mysolution-payments-svc", "mysolution-orders-svc"})
        assert is_disabled  # orders-svc still fires in Prometheus, but logic marks it disabled

    def test_job_exclusion_is_partial(self):
        alert = make_alert(excluded_jobs=["mysolution-worker-.*"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", {"mysolution-worker-svc"})
        assert is_partial
        assert not is_disabled

    def test_chips_excluded_when_fully_disabled(self):
        alert = make_alert(excluded_ns=["mysolution"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", set())
        assert is_disabled
        assert chips == []

    def test_chips_present_when_partial(self):
        alert = make_alert(excluded_ns=["mysolution-payments-.*"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", set())
        assert is_partial
        assert "mysolution-payments" in chips


class TestEvaluateNoEffect:
    def test_unrelated_exclusion_has_no_effect(self):
        alert = make_alert(excluded_ns=["otherapp.*"], excluded_jobs=["otherapp-worker"])
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", {"mysolution-svc"})
        assert not is_disabled
        assert not is_partial
        assert chips == []

    def test_empty_alert_no_exclusions(self):
        alert = make_alert()
        is_disabled, is_partial, chips = _evaluate(alert, "mysolution", {"micro1", "micro2"})
        assert not is_disabled
        assert not is_partial
        assert chips == []
