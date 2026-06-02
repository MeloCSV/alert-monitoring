from typing import List

from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.driven.postgres_repository.models.alert_api_model import AlertApiDB


class AlertApiDBMapper:

    def to_db(self, rule: AlertApi) -> AlertApiDB:
        return AlertApiDB(
            rule_id=rule.rule_id,
            name=rule.name,
            severity=rule.severity,
            notification_channel=rule.notification_channel,
            apis_alertadas=rule.apis_alertadas,
            message=rule.message,
        )

    def to_domain(self, rule_db: AlertApiDB) -> AlertApi:
        return AlertApi(
            rule_id=rule_db.rule_id,
            name=rule_db.name,
            severity=rule_db.severity,
            notification_channel=rule_db.notification_channel,
            apis_alertadas=rule_db.apis_alertadas or [],
            message=rule_db.message,
        )

    def to_domain_list(self, rules_db: List[AlertApiDB]) -> List[AlertApi]:
        return [self.to_domain(r) for r in rules_db]
