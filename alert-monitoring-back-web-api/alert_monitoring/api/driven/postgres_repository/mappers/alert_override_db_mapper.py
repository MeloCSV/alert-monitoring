from typing import List

from alert_monitoring.api.domain.models.alert_override import AlertOverride
from alert_monitoring.api.driven.postgres_repository.models.alert_override_model import AlertOverrideDB


class AlertOverrideDBMapper:

    def to_db(self, override: AlertOverride) -> AlertOverrideDB:
        return AlertOverrideDB(
            alert_name=override.alert_name,
            solution=override.solution,
            is_disabled=override.is_disabled,
            is_partial=override.is_partial,
            excluded_items=override.excluded_items,
        )

    def to_domain(self, db: AlertOverrideDB) -> AlertOverride:
        return AlertOverride(
            alert_name=db.alert_name,
            solution=db.solution,
            is_disabled=db.is_disabled,
            is_partial=db.is_partial,
            excluded_items=db.excluded_items or [],
        )

    def to_domain_list(self, items: List[AlertOverrideDB]) -> List[AlertOverride]:
        return [self.to_domain(i) for i in items]
