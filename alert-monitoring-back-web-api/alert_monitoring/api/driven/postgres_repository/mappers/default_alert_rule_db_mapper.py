from typing import List
from alert_monitoring.api.domain.models.default_alert_rule import DefaultAlertRule
from alert_monitoring.api.driven.postgres_repository.models.default_alert_rule_model import DefaultAlertRuleDB

class DefaultAlertRuleDBMapper:
    def to_db(self, rule: DefaultAlertRule) -> DefaultAlertRuleDB:
        return DefaultAlertRuleDB(
            cluster=rule.cluster,
            name=rule.name,
            display_name=rule.display_name,
            description=rule.description,
            severity=rule.severity,
            condition=rule.condition,
            environments=rule.environments,
            notification_channel=rule.notification_channel,
        )

    def to_domain(self, db: DefaultAlertRuleDB) -> DefaultAlertRule:
        return DefaultAlertRule(
            cluster=db.cluster,
            name=db.name,
            display_name=db.display_name,
            description=db.description,
            severity=db.severity,
            condition=db.condition,
            environments=db.environments or [],
            notification_channel=db.notification_channel,
        )

    def to_domain_list(self, dbs: List[DefaultAlertRuleDB]) -> List[DefaultAlertRule]:
        return [self.to_domain(d) for d in dbs]
