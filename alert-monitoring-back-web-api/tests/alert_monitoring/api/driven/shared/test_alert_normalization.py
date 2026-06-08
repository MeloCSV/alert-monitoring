import pytest
from dataclasses import dataclass
from typing import Any, Dict

from alert_monitoring.api.driven.shared.alert_normalization import (
    detect_environments,
    environments_or_all,
    extract_label_alternatives,
    build_exclusion_updates,
    clean_label_value,
    extract_adhoc_chips,
    _split_top_level_alternatives,
    display_canal,
    resolve_channels_from_labels,
    ALL_ENVIRONMENTS,
)


# ---------------------------------------------------------------------------
# detect_environments
# ---------------------------------------------------------------------------

class TestDetectEnvironments:
    def test_detects_pro(self):
        assert detect_environments(["namespace-pro"]) == ["pro"]

    def test_detects_dev(self):
        assert detect_environments(["my-service-dev"]) == ["dev"]

    def test_detects_multiple_envs_in_single_string(self):
        result = detect_environments(["dev|pre|pro"])
        assert "dev" in result
        assert "pre" in result
        assert "pro" in result

    def test_deduplicates_envs(self):
        result = detect_environments(["pro", "pro"])
        assert result.count("pro") == 1

    def test_skips_none_values(self):
        result = detect_environments([None, "pro"])
        assert result == ["pro"]

    def test_skips_empty_strings(self):
        result = detect_environments(["", "itg"])
        assert result == ["itg"]

    def test_returns_empty_for_no_match(self):
        assert detect_environments(["no-env-here"]) == []

    def test_case_insensitive(self):
        result = detect_environments(["PRO"])
        assert result == ["pro"]


# ---------------------------------------------------------------------------
# environments_or_all
# ---------------------------------------------------------------------------

class TestEnvironmentsOrAll:
    def test_returns_given_envs_when_not_empty(self):
        assert environments_or_all(["dev", "pro"]) == ["dev", "pro"]

    def test_returns_all_envs_when_empty(self):
        result = environments_or_all([])
        assert result == list(ALL_ENVIRONMENTS)

    def test_returns_all_envs_for_none_equivalent(self):
        result = environments_or_all([])
        assert "dev" in result
        assert "pro" in result


# ---------------------------------------------------------------------------
# extract_label_alternatives
# ---------------------------------------------------------------------------

class TestExtractLabelAlternatives:
    def test_extracts_positive_alternatives(self):
        expr = 'namespace=~"app-back|app-front"'
        result = extract_label_alternatives(expr, ["namespace"], exclude=False)
        assert "app-back" in result
        assert "app-front" in result

    def test_extracts_exclusion_alternatives(self):
        expr = 'namespace!~"excluded-a|excluded-b"'
        result = extract_label_alternatives(expr, ["namespace"], exclude=True)
        assert "excluded-a" in result
        assert "excluded-b" in result

    def test_returns_empty_for_no_match(self):
        expr = 'severity="critical"'
        result = extract_label_alternatives(expr, ["namespace"], exclude=False)
        assert result == []

    def test_returns_empty_for_none_expr(self):
        assert extract_label_alternatives(None, ["namespace"], exclude=False) == []

    def test_deduplicates_alternatives(self):
        expr = 'namespace=~"app" AND namespace=~"app"'
        result = extract_label_alternatives(expr, ["namespace"], exclude=False)
        assert result.count("app") == 1

    def test_multiple_keys(self):
        expr = 'namespace=~"app" AND job_name=~"worker"'
        result = extract_label_alternatives(expr, ["namespace", "job_name"], exclude=False)
        assert "app" in result
        assert "worker" in result


# ---------------------------------------------------------------------------
# build_exclusion_updates
# ---------------------------------------------------------------------------

@dataclass
class _FakeRule:
    alert: str
    expr: str
    labels: Dict[str, Any] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class TestBuildExclusionUpdates:
    def test_groups_by_raw_name(self):
        rules = [
            _FakeRule(alert="Default_Status rule1", expr='namespace!~"excl-a"'),
            _FakeRule(alert="Default_Status rule2", expr='namespace!~"excl-b"'),
        ]
        result = build_exclusion_updates(rules)
        assert "Default_Status" in result
        excl_ns, incl_ns, excl_jobs = result["Default_Status"]
        assert "excl-a" in excl_ns
        assert "excl-b" in excl_ns

    def test_empty_rules_returns_empty_dict(self):
        assert build_exclusion_updates([]) == {}

    def test_skips_rules_with_empty_alert(self):
        rules = [_FakeRule(alert="", expr='namespace!~"excl"')]
        result = build_exclusion_updates(rules)
        assert result == {}

    def test_extracts_included_namespaces(self):
        rules = [_FakeRule(alert="Default_Status", expr='namespace=~"incl-a|incl-b"')]
        result = build_exclusion_updates(rules)
        _, incl_ns, _ = result["Default_Status"]
        assert "incl-a" in incl_ns
        assert "incl-b" in incl_ns

    def test_extracts_excluded_jobs(self):
        rules = [_FakeRule(alert="Default_Status", expr='deployment!~"deploy-a"')]
        result = build_exclusion_updates(rules)
        _, _, excl_jobs = result["Default_Status"]
        assert "deploy-a" in excl_jobs


# ---------------------------------------------------------------------------
# clean_label_value
# ---------------------------------------------------------------------------

class TestCleanLabelValue:
    def test_strips_regex_anchors(self):
        assert clean_label_value("^my-app$") == "my-app"

    def test_strips_dotstar_suffix(self):
        assert clean_label_value("my-app.*") == "my-app"

    def test_strips_dotplus_suffix(self):
        assert clean_label_value("my-app.+") == "my-app"

    def test_strips_trailing_dash(self):
        assert clean_label_value("my-app-") == "my-app"

    def test_no_change_for_clean_value(self):
        assert clean_label_value("my-app") == "my-app"

    def test_strips_leading_whitespace(self):
        assert clean_label_value("  my-app") == "my-app"

    def test_strips_caret_only(self):
        assert clean_label_value("^value") == "value"


# ---------------------------------------------------------------------------
# extract_adhoc_chips
# ---------------------------------------------------------------------------

class TestExtractAdhocChips:
    def test_extracts_deployment_chip(self):
        expr = 'deployment=~"my-app-back|my-app-front"'
        result = extract_adhoc_chips(expr)
        assert "my-app-back" in result
        assert "my-app-front" in result

    def test_extracts_job_name_chip(self):
        expr = 'job_name=~"worker-job"'
        result = extract_adhoc_chips(expr)
        assert "worker-job" in result

    def test_returns_empty_for_none(self):
        assert extract_adhoc_chips(None) == []

    def test_returns_empty_for_empty_string(self):
        assert extract_adhoc_chips("") == []

    def test_deduplicates_chips(self):
        expr = 'deployment=~"app" AND deployment=~"app"'
        result = extract_adhoc_chips(expr)
        assert result.count("app") == 1

    def test_cleans_regex_suffixes(self):
        expr = 'deployment=~"my-app.*"'
        result = extract_adhoc_chips(expr)
        assert "my-app" in result


# ---------------------------------------------------------------------------
# _split_top_level_alternatives
# ---------------------------------------------------------------------------

class TestSplitTopLevelAlternatives:
    def test_splits_simple_pipe(self):
        assert _split_top_level_alternatives("a|b|c") == ["a", "b", "c"]

    def test_does_not_split_inside_parens(self):
        result = _split_top_level_alternatives("(a|b)|c")
        assert "(a|b)" in result
        assert "c" in result

    def test_single_value(self):
        assert _split_top_level_alternatives("only") == ["only"]

    def test_strips_whitespace(self):
        result = _split_top_level_alternatives(" a | b ")
        assert "a" in result
        assert "b" in result

    def test_empty_string(self):
        assert _split_top_level_alternatives("") == []


# ---------------------------------------------------------------------------
# display_canal
# ---------------------------------------------------------------------------

class TestDisplayCanal:
    def test_maps_msteams_to_teams(self):
        assert display_canal("msteams") == "Teams"

    def test_maps_omi_to_servicenow(self):
        assert display_canal("omi") == "ServiceNow"

    def test_returns_none_for_empty(self):
        assert display_canal("") is None

    def test_returns_none_for_none(self):
        assert display_canal(None) is None

    def test_case_insensitive(self):
        assert display_canal("OMI") == "ServiceNow"

    def test_unknown_canal_returns_as_is(self):
        assert display_canal("unknown-channel") == "unknown-channel"


# ---------------------------------------------------------------------------
# resolve_channels_from_labels
# ---------------------------------------------------------------------------

class TestResolveChannelsFromLabels:
    def test_resolves_msteams(self):
        result = resolve_channels_from_labels({"msteams": "true"})
        assert "Teams" in result

    def test_resolves_omi(self):
        result = resolve_channels_from_labels({"omi": "true"})
        assert "ServiceNow" in result

    def test_deduplicates_channels(self):
        result = resolve_channels_from_labels({"msteams": "true", "teams": "true"})
        assert result.count("Teams") == 1

    def test_empty_labels_returns_empty(self):
        assert resolve_channels_from_labels({}) == []

    def test_false_value_is_ignored(self):
        result = resolve_channels_from_labels({"msteams": "false"})
        assert "Teams" not in result
