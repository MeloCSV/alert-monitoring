from typing import List

from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi
from alert_monitoring.api.driven.postgres_repository.models.default_alert_api_model import DefaultAlertApiDB


class DefaultAlertApiDBMapper:

    def to_domain(self, db: DefaultAlertApiDB) -> DefaultAlertApi:
        return DefaultAlertApi(
            raw_name=db.raw_name,
            display_name=db.display_name,
            raw_description=db.raw_description,
            display_description=db.display_description,
            severity=db.severity,
            notification_channel=db.notification_channel,
            excluded_apis=db.excluded_apis or [],
        )

    def to_domain_list(self, items: List[DefaultAlertApiDB]) -> List[DefaultAlertApi]:
        return [self.to_domain(i) for i in items]
