import re
import logging
from typing import List, Tuple, Optional
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

        microservice, base_confidence = self._infer_microservice(rule)
        confidence = base_confidence if solution else max(0.0, base_confidence - 0.2)

        env_list, env_source = self._infer_environments(rule)
        if env_source == "expr":
            confidence = max(0.0, confidence - 0.15)
        elif env_source is None:
            confidence = max(0.0, confidence - 0.25)

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
            confidence_level=round(confidence, 2)
        )

    def _infer_channel(self, labels: dict) -> Optional[str]:
        if labels.get("canal"):
            return labels["canal"]
        if labels.get("msteams") == "true":
            return "msteams"
        if labels.get("omi") == "true":
            return "omi"
        if labels.get("jira") == "true":
            return "jira"
        return None

    def _infer_microservice(self, rule: PrometheusRule) -> Tuple[Optional[str], float]:
        labels = rule.labels
        expr = rule.expr

        if labels.get("service"):
            return labels["service"], 0.9
        if labels.get("namespace"):
            return labels["namespace"], 0.85
        if labels.get("job"):
            return labels["job"], 0.85

        if expr:
            job_match = re.search(r'job=(?:~)?["\']([^"\']+)["\']', expr)
            ns_match = re.search(r'namespace=(?:~)?["\']([^"\']+)["\']', expr)
            project_id_match = re.search(r'project_id=(?:~)?["\']([^"\']+)["\']', expr)

            if job_match:
                return self._clean(job_match.group(1)), 0.7
            if ns_match:
                return self._clean(ns_match.group(1)), 0.7
            if project_id_match:
                return self._clean(project_id_match.group(1)), 0,5

        if rule.group_name:
            return rule.group_name.replace(".rules", ""), 0.3

        return None, 0.0

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