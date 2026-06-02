from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from alert_monitoring.api.driving.api_rest.models.alert_api_response import AlertApiResponse


class DefaultAlertApiViewResponse(BaseModel):
    raw_name: str
    name: str
    description: Optional[str] = None
    severity: Optional[str] = None
    notification_channel: Optional[str] = None
    environments: List[str] = Field(default_factory=lambda: ["pro"])
    is_disabled: bool = False
    is_partial: bool = False
    chips: List[str] = Field(default_factory=list)


class ApiSolutionViewResponse(BaseModel):
    app: str
    default_alerts: List[DefaultAlertApiViewResponse] = Field(default_factory=list)
    adhoc_alerts: List[AlertApiResponse] = Field(default_factory=list)
    api_microservice_map: Dict[str, str] = Field(default_factory=dict)
    channels: List[str] = Field(default_factory=list)
