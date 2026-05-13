from pydantic import BaseModel


class AlertOverrideResponse(BaseModel):
    alert_name: str
    microservice: str
    is_disabled: bool
    is_partial: bool = False
