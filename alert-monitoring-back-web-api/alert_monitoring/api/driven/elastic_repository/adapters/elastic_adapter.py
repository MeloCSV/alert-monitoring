import json
import logging
import re
from typing import List, Optional
from typing import List
from alert_monitoring.api.driven.elastic_repository.models.elastic_model import ElasticRule

logger = logging.getLogger(__name__)

class ElasticAdapter:

    def load_rules(self, json_content: str) -> List[ElasticRule]:
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as exc:
            logger.error(f"Error al parsear el JSON de Elastic: {exc}")
            return []

        if not isinstance(data, dict) or "data" not in data:
            logger.warning("El contenido JSON no tiene la estructura esperada.")
            return []

        rules = []
        for item in data.get("data", []):
            try:
                rule = self._parse_rule(item)
                if rule:
                    rules.append(rule)
            except Exception as exc:
                logger.warning(f"Error procesando regla '{item.get('name', 'unknown')}': {exc}")
                continue

        return rules

    def _parse_rule(self, item: dict) -> ElasticRule:
        name = item.get("name", "")
        enabled = item.get("enabled", False)
        rule_type = item.get("rule_type_id", "")
        schedule_interval = item.get("schedule", {}).get("interval", "")
        condition = self._extract_condition(item.get("params", {}))

        document = self._extract_document(item)

        canal, severity, namespace, description, microservice, environment = self._extract_from_document(document)

        return ElasticRule(
            id=item.get("id", ""),
            name=name,
            enabled=enabled,
            schedule_interval=schedule_interval,
            condition=condition,
            canal=canal,
            severity=severity,
            namespace=namespace,
            description=description,
            microservice=microservice,
            environment=environment,
            rule_type=rule_type
        )

    def _extract_document(self, item: dict) -> dict:
        try:
            return item["actions"][0]["params"]["documents"][0]
        except (IndexError, KeyError):
            return {}

    def _extract_condition(self, params: dict) -> str:
        if "searchConfiguration" in params:
            return params["searchConfiguration"].get("query", {}).get("query", "")
        if "esQuery" in params:
            return params["esQuery"]
        if "esqlQuery" in params:
            return params["esqlQuery"].get("esql", "")
        return ""

    def _extract_from_document(self, doc: dict):
        if "alertManagerBody" in doc:
            labels = doc["alertManagerBody"].get("labels", {})
            annotations = doc["alertManagerBody"].get("annotations", {})
            canal = doc.get("canal")
            severity = labels.get("severity")
            namespace = labels.get("namespace")
            description = self._clean_template(annotations.get("message"))
            microservice = self._clean_template(labels.get("application") or labels.get("job"))
            environment = labels.get("environment")
            return canal, severity, namespace, description, microservice, environment

        canal = doc.get("canal")
        severity = doc.get("severity")
        namespace = doc.get("namespace")
        description = self._clean_template(doc.get("message_info"))
        microservice = self._clean_template(doc.get("pod") or doc.get("namespace"))
        environment = doc.get("environment")
        return canal, severity, namespace, description, microservice, environment
        

    def _clean_template(self, value: str) -> Optional[str]:
        if not value:
            return None
        # Si el valor es puro template devuelve None
        if re.match(r'^\{\{.*\}\}$', value.strip()):
            return None
        # Limpia HTML
        value = re.sub(r'<[^>]+>', '', value)
        # Limpia templates mustache
        value = re.sub(r'\{\{[^}]+\}\}', '', value).strip()
        return value if value else None