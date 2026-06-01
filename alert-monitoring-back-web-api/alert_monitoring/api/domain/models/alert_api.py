from typing import List, Optional

from pydantic import BaseModel, Field


class AlertApi(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    api: str = Field(..., description="Nombre/ruta de la API alarmada")
    microservice: str = Field(..., description="Microservicio que expone la API")
    severity: Optional[str] = None
    notification_channel: Optional[str] = None
    environments: List[str] = Field(default_factory=list)
