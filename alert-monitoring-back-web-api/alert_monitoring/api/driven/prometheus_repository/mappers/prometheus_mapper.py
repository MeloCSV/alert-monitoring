import re
from typing import List, Optional

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.default_alert_rule import DefaultAlertRule
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule
from alert_monitoring.api.driven.shared.alert_normalization import (
    BOOL_CHANNEL_LABELS,
    DEFAULT_ALERT_DISPLAY,
    display_canal,
    environments_or_all,
)


class PrometheusMapper:
    def to_domain(self, rules: List[PrometheusRule]) -> List[Alert]:
        return [self._map_rule(rule) for rule in rules if not self._is_default(rule)]

    def to_catalog(self, rules: List[PrometheusRule]) -> List[DefaultAlertRule]:
        return [self._map_default_rule(rule) for rule in rules if self._is_default(rule)]

    def _is_default(self, rule: PrometheusRule) -> bool:
        return str(rule.labels.get("alertype", "")).lower() == "default"

    def _map_rule(self, rule: PrometheusRule) -> Alert:
        labels = rule.labels

        return Alert(
            name=rule.alert,
            description=rule.annotations.get("message", "Sin descripción"),
            source_tool="Prometheus",
            severity=labels.get("severity", "unknown"),
            condition=rule.expr,
            environments=environments_or_all(self._infer_environments(rule)),
            microservice=self._infer_microservice(rule),
            solution=self._infer_solution(rule),
            notification_channel=self._infer_channel(labels),
            alert_type="Ad-hoc",
            cluster=rule.cluster_name or None,
        )

    def _map_default_rule(self, rule: PrometheusRule) -> DefaultAlertRule:
        labels = rule.labels
        raw_name = rule.alert.split()[0] if rule.alert else rule.alert
        display = DEFAULT_ALERT_DISPLAY.get(raw_name)
        display_name = display[0] if display else raw_name
        description = display[1] if display else rule.annotations.get("message", "Sin descripción")

        return DefaultAlertRule(
            name=raw_name,
            display_name=display_name,
            description=description,
            severity=labels.get("severity", "unknown"),
            condition=rule.expr,
            environments=environments_or_all(self._infer_environments(rule)),
            notification_channel=self._infer_channel(labels),
            cluster=rule.cluster_name or "unknown",
        )

    def _infer_solution(self, rule: PrometheusRule) -> str:
        solucion = rule.labels.get("solucion")
        if solucion:
            return solucion
        group_name = rule.group_name or ""
        cleaned = re.sub(r"\.rules$", "", group_name)
        cleaned = re.sub(r"-cr[ií]ticas$", "", cleaned)
        return cleaned or "unknown"

    def _infer_channel(self, labels: dict) -> Optional[str]:
        canal = labels.get("canal")
        if canal:
            return display_canal(canal)
        for label, display in BOOL_CHANNEL_LABELS:
            if labels.get(label) == "true":
                return display
        return None

    def _infer_microservice(self, rule: PrometheusRule) -> Optional[str]:
        labels = rule.labels
        for key in ("service", "namespace", "job"):
            if labels.get(key):
                return labels[key]

        if rule.expr:
            for key in ("job", "namespace", "project_id"):
                match = re.search(rf'{key}=(?:~)?["\']([^"\']+)["\']', rule.expr)
                if match:
                    return self._clean(match.group(1))

        if rule.group_name:
            return rule.group_name.replace(".rules", "")
        return None

    def _infer_environments(self, rule: PrometheusRule) -> List[str]:
        labels = rule.labels

        label_envs = [
            val for val in (labels.get(key, "").lower() for key in ("environment", "env"))
            if val and "{{" not in val
        ]
        if label_envs:
            return label_envs

        expr_envs: set[str] = set()
        for match in re.findall(r'environment(?:=~|=)["\']([^"\']+)["\']', rule.expr):
            for part in match.split("|"):
                clean = self._clean(part)
                if clean:
                    expr_envs.add(clean)
        return list(expr_envs)

    def _clean(self, value: str) -> str:
        return value.replace(".*", "").replace(".+", "").replace("^", "").replace("$", "").strip()
