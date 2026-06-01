from typing import List

from alert_monitoring.api.domain.models.alert_api_disabled import AlertApiDisabled
from alert_monitoring.api.driven.postgres_repository.models.alert_api_disabled_model import AlertApiDisabledDB


class AlertApiDisabledDBMapper:

    def to_db(self, disabled: AlertApiDisabled) -> AlertApiDisabledDB:
        return AlertApiDisabledDB(
            alert_name=disabled.alert_name,
            api=disabled.api,
            is_disabled=disabled.is_disabled,
            is_partial=disabled.is_partial,
            excluded_items=disabled.excluded_items,
        )

    def to_domain(self, db: AlertApiDisabledDB) -> AlertApiDisabled:
        return AlertApiDisabled(
            alert_name=db.alert_name,
            api=db.api,
            is_disabled=db.is_disabled,
            is_partial=db.is_partial,
            excluded_items=db.excluded_items or [],
        )

    def to_domain_list(self, items: List[AlertApiDisabledDB]) -> List[AlertApiDisabled]:
        return [self.to_domain(i) for i in items]
