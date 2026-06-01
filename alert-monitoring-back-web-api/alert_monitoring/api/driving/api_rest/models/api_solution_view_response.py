from typing import List, Optional

from pydantic import BaseModel, Field


class AlertApiResponse(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    api: str
    microservice: str
    severity: Optional[str] = None
    notification_channel: Optional[str] = None
    environments: List[str] = Field(default_factory=list)


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
    channels: List[str] = Field(default_factory=list)
