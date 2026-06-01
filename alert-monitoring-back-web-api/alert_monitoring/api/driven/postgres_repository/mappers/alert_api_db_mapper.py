from typing import List

from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.driven.postgres_repository.models.alert_api_model import AlertApiDB


class AlertApiDBMapper:

    def to_db(self, alert: AlertApi) -> AlertApiDB:
        return AlertApiDB(
            name=alert.name,
            description=alert.description,
            api=alert.api,
            microservice=alert.microservice,
            severity=alert.severity,
            notification_channel=alert.notification_channel,
            environments=alert.environments,
        )

    def to_domain(self, db: AlertApiDB) -> AlertApi:
        return AlertApi(
            id=db.id,
            name=db.name,
            description=db.description,
            api=db.api,
            microservice=db.microservice,
            severity=db.severity,
            notification_channel=db.notification_channel,
            environments=db.environments or [],
        )

    def to_domain_list(self, items: List[AlertApiDB]) -> List[AlertApi]:
        return [self.to_domain(i) for i in items]
