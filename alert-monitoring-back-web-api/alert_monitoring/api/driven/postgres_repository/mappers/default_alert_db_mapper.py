from typing import List

from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.driven.postgres_repository.models.default_alert_model import DefaultAlertDB


class DefaultAlertDBMapper:

    def to_domain(self, db: DefaultAlertDB) -> DefaultAlert:
        return DefaultAlert(
            raw_name=db.raw_name,
            display_name=db.display_name,
            raw_description=db.raw_description,
            display_description=db.display_description,
            severity=db.severity,
            notification_channel=db.notification_channel,
            excluded_namespaces=db.excluded_namespaces or [],
            included_namespaces=db.included_namespaces or [],
            excluded_jobs=db.excluded_jobs or [],
        )

    def to_domain_list(self, items: List[DefaultAlertDB]) -> List[DefaultAlert]:
        return [self.to_domain(i) for i in items]
