import re
import logging
from typing import List, Optional, Tuple
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule
from alert_monitoring.api.domain.models.alert import Alert

logger = logging.getLogger(__name__)

class PrometheusMapper:
    def to_domain(self, rules: List[PrometheusRule]) -> List[Alert]:
        return [self._map_rule(rule) for rule in rules]

    def _map_rule(self, rule: PrometheusRule) -> Alert:
        labels = rule.labels
        annotations = rule.annotations

        description = annotations.get("message", "Sin descripción")
        severity = labels.get("severity", "unknown")
        solution = labels.get("solucion", "unknown")
        channel = self._infer_channel(labels)

        microservice = self._infer_microservice(rule)
        env_list, _ = self._infer_environments(rule)

        is_default = str(labels.get("alertype", "")).lower() == "default"
        alert_type = "Por Defecto" if is_default else "Ad-hoc"

        excluded_namespaces = None
        included_namespaces = None
        if is_default:
            excluded_namespaces = self._extract_namespace_pattern(rule.expr, exclude=True)
            included_namespaces = self._extract_namespace_pattern(rule.expr, exclude=False)

        return Alert(
            name=rule.alert,
            description=description,
            source_tool="Prometheus",
            severity=severity,
            condition=rule.expr,
            environments=env_list,
            microservice=microservice,
            solution=solution,
            notification_channel=channel,
            alert_type=alert_type,
            excluded_namespaces=excluded_namespaces,
            included_namespaces=included_namespaces,
        )

    _NAMESPACE_LABEL_KEYS = ("namespace", "backend_target_name", "backend_name")

    def _extract_namespace_pattern(self, expr: str, exclude: bool) -> Optional[str]:
        if not expr:
            return None
        operator = "!~" if exclude else "=~"
        patterns: list[str] = []
        for key in self._NAMESPACE_LABEL_KEYS:
            regex = rf'{key}\s*{re.escape(operator)}\s*"([^"]+)"'
            for match in re.findall(regex, expr):
                if match not in patterns:
                    patterns.append(match)
        if not patterns:
            return None
        return "|".join(patterns)
    _CANAL_DISPLAY_NAMES = {
        "msteams": "Teams",
        "omi": "ServiceNow",
        "jira": "Jira",
    }

    def _infer_channel(self, labels: dict) -> Optional[str]:
        canal = labels.get("canal")
        if canal:
            return self._CANAL_DISPLAY_NAMES.get(canal.lower(), canal)
        if labels.get("msteams") == "true":
            return "Teams"
        if labels.get("omi") == "true":
            return "ServiceNow"
        if labels.get("jira") == "true":
            return "Jira"
        if labels.get("mail") == "true":
            return "Mail"
        return None

    def _infer_microservice(self, rule: PrometheusRule) -> Optional[str]:
        labels = rule.labels
        expr = rule.expr

        if labels.get("service"):
            return labels["service"]
        if labels.get("namespace"):
            return labels["namespace"]
        if labels.get("job"):
            return labels["job"]

        if expr:
            job_match = re.search(r'job=(?:~)?["\']([^"\']+)["\']', expr)
            ns_match = re.search(r'namespace=(?:~)?["\']([^"\']+)["\']', expr)
            project_id_match = re.search(r'project_id=(?:~)?["\']([^"\']+)["\']', expr)

            if job_match:
                return self._clean(job_match.group(1))
            if ns_match:
                return self._clean(ns_match.group(1))
            if project_id_match:
                return self._clean(project_id_match.group(1))

        if rule.group_name:
            return rule.group_name.replace(".rules", "")

        return None

    def _infer_environments(self, rule: PrometheusRule) -> Tuple[list, Optional[str]]:
        labels = rule.labels
        expr = rule.expr

        label_envs = []
        for key in ["environment", "env"]:
            val = labels.get(key, "").lower()
            if val and "{{" not in val:
                label_envs.append(val)
        if label_envs:
            return label_envs, "label"

        expr_envs = set()
        for match in re.findall(r'environment(?:=~|=)["\']([^"\']+)["\']', expr):
            for part in re.split(r'\|', match):
                clean = self._clean(part)
                if clean:
                    expr_envs.add(clean)
        if expr_envs:
            return list(expr_envs), "expr"

        return [], None

    def _clean(self, value: str) -> str:
        return value.replace(".*", "").replace(".+", "").replace("^", "").replace("$", "").strip()