from pydantic import BaseModel
from typing import List
from alert_monitoring.api.driving.api_rest.models.alert_response import AlertResponse

class UploadYamlRequest(BaseModel):
    yaml_content: str

class AlertListResponse(BaseModel):
    total: int
    alerts: List[AlertResponse]