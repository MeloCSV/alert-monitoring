from typing import List
from alert_monitoring.api.driving.api_rest.models.alert_response import AlertResponse
from alert_monitoring.api.domain.models.alert import Alert


class AlertDTOMapper:

    def to_model_decorator(self, alert: Alert) -> AlertResponse:
        return AlertResponse(
            name=alert.name,
            description=alert.description,
            source_tool=alert.source_tool or "unknown",
            severity=alert.severity,
            condition=alert.condition,
            environments=alert.environments or [],
            microservice=alert.microservice,
            solution=alert.solution,
            notification_channel=alert.notification_channel,
            alert_type=alert.alert_type,
            is_overridden=alert.is_overridden,
            excluded_namespaces=alert.excluded_namespaces,
            included_namespaces=alert.included_namespaces,
        )

    def to_models_decorator(self, alerts: List[Alert]) -> List[AlertResponse]:
        return [self.to_model_decorator(a) for a in alerts]
