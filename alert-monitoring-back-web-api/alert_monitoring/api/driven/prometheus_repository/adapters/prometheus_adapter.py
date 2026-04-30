import yaml
import logging
from typing import List
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule

logger = logging.getLogger(__name__)

class PrometheusAdapter:
    def load_rules(self, yaml_content: str) -> List[PrometheusRule]:
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as exc:
            logger.error(f"Error al parsear el YAML de Prometheus: {exc}")
            return []

        if not data or not isinstance(data, dict):
            logger.warning("El contenido del YAML está vacío o no es un diccionario válido.")
            return []

        rules = []
        for group in data.get("spec", {}).get("groups", []):
            group_name = group.get("name", "")
            for rule in group.get("rules", []):
                if "alert" not in rule:
                    continue
                rules.append(PrometheusRule(
                    alert=rule.get("alert"),
                    expr=rule.get("expr", ""),
                    labels=rule.get("labels", {}),
                    annotations=rule.get("annotations", {}),
                    group_name=group_name
                ))
        return rules