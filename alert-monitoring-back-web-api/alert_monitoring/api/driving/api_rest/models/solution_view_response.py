from typing import List, Optional

from pydantic import BaseModel, Field

from alert_monitoring.api.driving.api_rest.models.alert_response import AlertResponse
from alert_monitoring.api.driving.api_rest.models.blackout_response import BlackoutResponse


class DefaultAlertViewResponse(BaseModel):
    raw_name: str
    name: str
    description: Optional[str] = None
    severity: Optional[str] = None
    notification_channel: Optional[str] = None
    environments: List[str] = Field(default_factory=lambda: ["pro"])
    is_overridden: bool = False
    is_partial: bool = False
    chips: List[str] = Field(default_factory=list)


class SolutionViewResponse(BaseModel):
    solution: str
    default_alerts: List[DefaultAlertViewResponse] = Field(default_factory=list)
    adhoc_alerts: List[AlertResponse] = Field(default_factory=list)
    blackouts: List[BlackoutResponse] = Field(default_factory=list)
    channels: List[str] = Field(default_factory=list)
