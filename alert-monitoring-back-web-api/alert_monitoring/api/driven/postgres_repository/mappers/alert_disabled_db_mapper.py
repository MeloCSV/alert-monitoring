from typing import List

from alert_monitoring.api.domain.models.alert_disabled import AlertDisabled
from alert_monitoring.api.driven.postgres_repository.models.alert_disabled_model import AlertDisabledDB


class AlertDisabledDBMapper:

    def to_db(self, disabled: AlertDisabled) -> AlertDisabledDB:
        return AlertDisabledDB(
            alert_name=disabled.alert_name,
            solution=disabled.solution,
            is_disabled=disabled.is_disabled,
            is_partial=disabled.is_partial,
            excluded_items=disabled.excluded_items,
        )

    def to_domain(self, db: AlertDisabledDB) -> AlertDisabled:
        return AlertDisabled(
            alert_name=db.alert_name,
            solution=db.solution,
            is_disabled=db.is_disabled,
            is_partial=db.is_partial,
            excluded_items=db.excluded_items or [],
        )

    def to_domain_list(self, items: List[AlertDisabledDB]) -> List[AlertDisabled]:
        return [self.to_domain(i) for i in items]
