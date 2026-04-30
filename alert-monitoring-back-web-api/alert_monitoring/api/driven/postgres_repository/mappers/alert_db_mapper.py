from typing import List

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.driven.postgres_repository.models.alert_model import AlertDB

class AlertDBMapper:

    def to_db(self, alert: Alert) -> AlertDB:
        return AlertDB(
            name=alert.name,
            description=alert.description,
            source_tool=alert.source_tool,
            severity=alert.severity,
            condition=alert.condition,
            environments=alert.environments,
            microservice=alert.microservice,
            solution=alert.solution,
            notification_channel=alert.notification_channel,
            confidence_level=alert.confidence_level
        )

    def to_domain(self, alert_db: AlertDB) -> Alert:
        return Alert(
            name=alert_db.name,
            description=alert_db.description,
            source_tool=alert_db.source_tool,
            severity=alert_db.severity,
            condition=alert_db.condition,
            environments=alert_db.environments or [],
            microservice=alert_db.microservice,
            solution=alert_db.solution,
            notification_channel=alert_db.notification_channel,
            confidence_level=alert_db.confidence_level
        )
    # alert_db_mapper.py — añadir este método
    def to_domain_list(self, alerts_db: List[AlertDB]) -> List[Alert]:
        return [self.to_domain(a) for a in alerts_db]