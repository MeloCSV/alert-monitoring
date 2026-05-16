import logging
import re
from typing import Dict, List, Optional, Tuple

from alert_monitoring.api.driven.elastic_repository.models.elastic_model import ElasticRule
from alert_monitoring.api.driven.shared.alert_normalization import detect_environments

logger = logging.getLogger(__name__)

_TEMPLATE_FULL = re.compile(r"^\s*\{\{[^{}]+\}\}\s*$")
_TEMPLATE_INLINE = re.compile(r"\{\{[^}]+\}\}")
_HTML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


class ElasticAdapter:

    def parse_rules(self, items: List[dict]) -> List[ElasticRule]:
        rules: List[ElasticRule] = []
        for item in items:
            try:
                rule = self._parse_rule(item)
                if rule:
                    rules.append(rule)
            except Exception as exc:
                logger.warning(f"Error procesando regla '{item.get('name', 'unknown')}': {exc}")
                continue
        return rules

    def _parse_rule(self, item: dict) -> ElasticRule:
        params = item.get("params", {})
        condition = self._extract_condition(params)
        labels, canals, description = self._collect_from_actions(item.get("actions", []))
        environments = self._extract_environments(labels, condition, params)

        return ElasticRule(
            id=item.get("id", ""),
            name=item.get("name", ""),
            enabled=item.get("enabled", False),
            schedule_interval=item.get("schedule", {}).get("interval", ""),
            condition=condition,
            rule_type=item.get("rule_type_id", ""),
            canals=canals,
            labels=labels,
            description=description,
            environments=environments,
        )

    def _collect_from_actions(self, actions: List[dict]) -> Tuple[Dict[str, str], List[str], Optional[str]]:
        labels: Dict[str, str] = {}
        canals: List[str] = []
        description: Optional[str] = None

        for action in actions:
            params = action.get("params") or {}

            for doc in params.get("documents") or []:
                self._merge_document(doc, labels, canals)
                description = description or self._extract_description(doc)

            if not params.get("documents"):
                description = description or self._clean_template(params.get("message"))
                if params.get("level"):
                    labels.setdefault("severity", str(params["level"]))

        return labels, canals, description

    def _merge_document(self, doc: dict, labels: Dict[str, str], canals: List[str]) -> None:
        canal = self._clean_template(doc.get("canal"))
        if canal and canal not in canals:
            canals.append(canal)

        alert_manager_body = doc.get("alertManagerBody")
        if isinstance(alert_manager_body, dict):
            for key, value in (alert_manager_body.get("labels") or {}).items():
                cleaned = self._clean_template(value)
                if cleaned and key not in labels:
                    labels[key] = cleaned
            return

        flat_label_keys = (
            "severity", "namespace", "pod", "cluster", "cloud",
            "instance", "job", "level", "alertname", "deployment",
            "application", "environment",
        )
        for key in flat_label_keys:
            if key in doc and key not in labels:
                cleaned = self._clean_template(doc.get(key))
                if cleaned:
                    labels[key] = cleaned

    def _extract_description(self, doc: dict) -> Optional[str]:
        alert_manager_body = doc.get("alertManagerBody")
        if isinstance(alert_manager_body, dict):
            annotations = alert_manager_body.get("annotations") or {}
            cleaned = self._clean_template(annotations.get("message"))
            if cleaned:
                return cleaned

        for key in ("message_info", "message", "context_message"):
            cleaned = self._clean_template(doc.get(key))
            if cleaned:
                return cleaned
        return None

    def _extract_condition(self, params: dict) -> str:
        search_config = params.get("searchConfiguration")
        if isinstance(search_config, dict):
            return search_config.get("query", {}).get("query", "") or ""
        if "esQuery" in params:
            return params.get("esQuery") or ""
        esql = params.get("esqlQuery")
        if isinstance(esql, dict):
            return esql.get("esql", "") or ""
        return ""

    def _extract_environments(self, labels: Dict[str, str], condition: str, params: dict) -> List[str]:
        sources: List[Optional[str]] = [labels.get("environment"), condition]

        search_config = params.get("searchConfiguration") or {}
        index = search_config.get("index")
        if isinstance(index, dict):
            sources.append(index.get("title"))
        elif isinstance(index, str):
            sources.append(index)

        param_index = params.get("index")
        if isinstance(param_index, list):
            sources.extend(str(i) for i in param_index)
        elif isinstance(param_index, str):
            sources.append(param_index)

        return detect_environments(sources)

    def _clean_template(self, value) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if _TEMPLATE_FULL.match(text):
            return None
        text = _HTML_TAG.sub(" ", text)
        text = _TEMPLATE_INLINE.sub(" ", text)
        text = _WHITESPACE.sub(" ", text).strip()
        return text or None
