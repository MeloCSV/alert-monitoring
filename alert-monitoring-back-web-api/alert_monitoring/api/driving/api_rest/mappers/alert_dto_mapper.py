from typing import List
from fwkpy_lib_core.synchronous.mappers.decorators import mapping
from alert_monitoring.api.driving.api_rest.models.alert_response import AlertResponse
from alert_monitoring.api.domain.models.alert import Alert


class AlertDTOMapper:

    @mapping([])
    def to_model_decorator(self, alert: Alert) -> AlertResponse:
        pass

    @mapping([])
    def to_models_decorator(self, alerts: List[Alert]) -> List[AlertResponse]:
        pass