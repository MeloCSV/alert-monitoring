import pytest
from alert_monitoring.api.application.use_cases.recompute_overrides_use_case import (
    _evaluate,
    _regex_matches,
    build_exclusion_updates,
)
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.driven.shared.alert_normalization import extract_label_alternatives, NAMESPACE_LABEL_KEYS


# PromQL expr that mirrors the real Default_High_4xx_Http_Requests_Principal rule.
# Note: .*ccp.* appears only in the numerator exclusion, not in the denominator.
_4XX_EXPR_CCP_NUMERATOR_ONLY = (
    'sum(increase(metric{response_code=~"4.*",'
    ' backend_target_name!~".*serve404.*|.*ccp.*|.*demo.*",'
    ' project_id="pro"}[5m])) by (backend_target_name)'
    ' / sum(increase(metric{'
    ' backend_target_name!~".*serve404.*|.*demo.*",'
    ' project_id="pro"}[5m])) by (backend_target_name) * 100 > 5'
)

# Symmetric expr where .*ccp.* appears in BOTH numerator and denominator.
_4XX_EXPR_CCP_BOTH = (
    'sum(increase(metric{response_code=~"4.*",'
    ' backend_target_name!~".*serve404.*|.*ccp.*|.*demo.*",'
    ' project_id="pro"}[5m])) by (backend_target_name)'
    ' / sum(increase(metric{'
    ' backend_target_name!~".*serve404.*|.*ccp.*|.*demo.*",'
    ' project_id="pro"}[5m])) by (backend_target_name) * 100 > 5'
)


class TestRegexMatches:
    def test_ccp_matches_wildcard_pattern(self):
        assert _regex_matches("ccp", ".*ccp.*") is True

    def test_ccp_service_matches_wildcard_pattern(self):
        assert _regex_matches("ccp-api-service", ".*ccp.*") is True

    def test_unrelated_name_does_not_match_ccp_pattern(self):
        assert _regex_matches("myapp", ".*ccp.*") is False

    def test_serve404_matches_own_pattern(self):
        assert _regex_matches("serve404", ".*serve404.*") is True

    def test_invalid_regex_returns_false(self):
        assert _regex_matches("anything", "[invalid") is False


class TestExtractLabelAlternatives:
    def test_extracts_ccp_from_numerator_only_expr(self):
        alts = extract_label_alternatives(_4XX_EXPR_CCP_NUMERATOR_ONLY, NAMESPACE_LABEL_KEYS, exclude=True)
        assert ".*ccp.*" in alts

    def test_extracts_ccp_from_symmetric_expr(self):
        alts = extract_label_alternatives(_4XX_EXPR_CCP_BOTH, NAMESPACE_LABEL_KEYS, exclude=True)
        assert ".*ccp.*" in alts

    def test_does_not_include_ccp_in_inclusions(self):
        alts = extract_label_alternatives(_4XX_EXPR_CCP_BOTH, NAMESPACE_LABEL_KEYS, exclude=False)
        assert ".*ccp.*" not in alts

    def test_collects_all_unique_patterns_from_multiple_selectors(self):
        alts = extract_label_alternatives(_4XX_EXPR_CCP_NUMERATOR_ONLY, NAMESPACE_LABEL_KEYS, exclude=True)
        assert ".*serve404.*" in alts
        assert ".*demo.*" in alts
        assert ".*ccp.*" in alts


class TestEvaluate:
    def _make_alert(self, excluded_namespaces, included_namespaces=None, excluded_jobs=None):
        return DefaultAlert(
            raw_name="Default_High_4xx_Http_Requests_Principal",
            display_name="Alto porcentaje de errores HTTP 4xx (>5%)",
            excluded_namespaces=excluded_namespaces,
            included_namespaces=included_namespaces or [],
            excluded_jobs=excluded_jobs or [],
        )

    def test_ccp_is_disabled_when_excluded_by_wildcard(self):
        alert = self._make_alert([".*ccp.*", ".*demo.*"])
        is_disabled, is_partial, excluded_items = _evaluate(alert, "ccp", set())
        assert is_disabled is True
        assert is_partial is False
        assert excluded_items == []

    def test_unrelated_solution_is_not_disabled(self):
        alert = self._make_alert([".*ccp.*", ".*demo.*"])
        is_disabled, is_partial, excluded_items = _evaluate(alert, "myapp", set())
        assert is_disabled is False
        assert is_partial is False

    def test_ccp_is_disabled_when_exclusion_is_from_numerator_only(self):
        """
        Even if .*ccp.* only appears in the numerator exclusion of the PromQL expr,
        extract_label_alternatives uses a union of all backend_target_name!~ selectors,
        so the pattern is still detected and the solution is marked disabled.
        """
        alts = extract_label_alternatives(_4XX_EXPR_CCP_NUMERATOR_ONLY, NAMESPACE_LABEL_KEYS, exclude=True)
        alert = self._make_alert(alts)
        is_disabled, is_partial, _ = _evaluate(alert, "ccp", set())
        assert is_disabled is True

    def test_partial_exclusion_when_microservice_prefix_matches(self):
        alert = self._make_alert(["ccp-service-.*"])
        is_disabled, is_partial, excluded_items = _evaluate(alert, "ccp", set())
        assert is_disabled is False
        assert is_partial is True
        assert "ccp-service" in excluded_items

    def test_re_inclusion_overrides_full_exclusion(self):
        alert = self._make_alert(
            excluded_namespaces=[".*ccp.*"],
            included_namespaces=[".*ccp.*"],
        )
        is_disabled, is_partial, _ = _evaluate(alert, "ccp", set())
        assert is_disabled is False

    def test_ccp_microservice_triggers_full_exclusion(self):
        alert = self._make_alert([".*ccp.*"])
        is_disabled, is_partial, _ = _evaluate(alert, "other", {"ccp-api"})
        assert is_disabled is True

    def test_no_exclusion_means_not_disabled_not_partial(self):
        alert = self._make_alert([])
        is_disabled, is_partial, excluded_items = _evaluate(alert, "ccp", set())
        assert is_disabled is False
        assert is_partial is False
        assert excluded_items == []


class TestBuildExclusionUpdates:
    def _make_rule(self, prometheus_name, condition, description="", severity="principal", channel="ServiceNow"):
        from alert_monitoring.api.domain.models.alert import Alert
        return Alert(
            name=prometheus_name,
            prometheus_name=prometheus_name,
            condition=condition,
            description=description,
            source_tool="Prometheus",
            severity=severity,
            notification_channel=channel,
            alert_type="Por Defecto",
            environments=["pro"],
        )

    def test_build_extracts_ccp_from_4xx_rule(self):
        rule = self._make_rule("Default_High_4xx_Http_Requests_Principal", _4XX_EXPR_CCP_BOTH)
        result = build_exclusion_updates([rule])
        excl_ns, incl_ns, excl_jobs = result["Default_High_4xx_Http_Requests_Principal"]
        assert ".*ccp.*" in excl_ns
        assert incl_ns == []
        assert excl_jobs == []

    def test_build_extracts_ccp_even_from_numerator_only_expr(self):
        rule = self._make_rule("Default_High_4xx_Http_Requests_Principal", _4XX_EXPR_CCP_NUMERATOR_ONLY)
        result = build_exclusion_updates([rule])
        excl_ns, _, _ = result["Default_High_4xx_Http_Requests_Principal"]
        assert ".*ccp.*" in excl_ns

    def test_build_merges_multiple_rules_with_same_name(self):
        rule1 = self._make_rule("Default_High_4xx_Http_Requests_Principal", _4XX_EXPR_CCP_BOTH)
        rule2 = self._make_rule(
            "Default_High_4xx_Http_Requests_Principal",
            'sum(increase(metric{backend_target_name!~".*newexclusion.*"}[5m]))',
        )
        result = build_exclusion_updates([rule1, rule2])
        excl_ns, _, _ = result["Default_High_4xx_Http_Requests_Principal"]
        assert ".*ccp.*" in excl_ns
        assert ".*newexclusion.*" in excl_ns

    def test_build_ignores_rules_without_prometheus_name(self):
        rule = self._make_rule("any-name", _4XX_EXPR_CCP_BOTH)
        rule.prometheus_name = None
        result = build_exclusion_updates([rule])
        assert result == {}
