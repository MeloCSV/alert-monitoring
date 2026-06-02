from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from alert_monitoring.api.domain.models.alert_api import AlertApi


class DefaultAlertApiView(BaseModel):
    raw_name: str
    name: str
    description: Optional[str] = None
    severity: Optional[str] = None
    notification_channel: Optional[str] = None
    environments: List[str] = Field(default_factory=lambda: ["pro"])
    is_disabled: bool = False
    is_partial: bool = False
    chips: List[str] = Field(default_factory=list)


class ApiSolutionView(BaseModel):
    app: str
    default_alerts: List[DefaultAlertApiView] = Field(default_factory=list)
    adhoc_alerts: List[AlertApi] = Field(default_factory=list)
    api_microservice_map: Dict[str, str] = Field(default_factory=dict)
    channels: List[str] = Field(default_factory=list)
