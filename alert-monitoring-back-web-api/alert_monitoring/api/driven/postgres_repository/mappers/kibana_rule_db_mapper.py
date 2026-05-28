from datetime import datetime
from typing import List, Optional

from alert_monitoring.api.domain.models.kibana_rule import KibanaRule
from alert_monitoring.api.driven.postgres_repository.models.kibana_rule_model import KibanaRuleDB


class KibanaRuleDBMapper:

    def to_db(self, rule: KibanaRule) -> KibanaRuleDB:
        return KibanaRuleDB(
            rule_id=rule.rule_id,
            name=rule.name,
            enabled=rule.enabled,
            tags=rule.tags,
            schedule_interval=rule.schedule_interval,
            severity=rule.severity,
            notification_channels=rule.notification_channels,
            apis=rule.apis,
            disabled_apis=rule.disabled_apis,
            is_global=rule.is_global,
            last_execution_date=self._parse_date(rule.last_execution_date),
            last_execution_status=rule.last_execution_status,
            kibana_url=rule.kibana_url,
            kibana_name=rule.kibana_name,
            message=rule.message,
        )

    def to_domain(self, rule_db: KibanaRuleDB) -> KibanaRule:
        return KibanaRule(
            rule_id=rule_db.rule_id,
            name=rule_db.name,
            enabled=rule_db.enabled,
            tags=rule_db.tags or [],
            schedule_interval=rule_db.schedule_interval,
            severity=rule_db.severity,
            notification_channels=rule_db.notification_channels or [],
            apis=rule_db.apis or [],
            disabled_apis=rule_db.disabled_apis or [],
            is_global=rule_db.is_global,
            last_execution_date=rule_db.last_execution_date.isoformat() if rule_db.last_execution_date else None,
            last_execution_status=rule_db.last_execution_status,
            kibana_url=rule_db.kibana_url,
            kibana_name=rule_db.kibana_name,
            message=rule_db.message,
        )

    def to_domain_list(self, rules_db: List[KibanaRuleDB]) -> List[KibanaRule]:
        return [self.to_domain(r) for r in rules_db]

    def _parse_date(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
