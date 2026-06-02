from pydantic import BaseModel, Field
from typing import List, Optional


class AlertApi(BaseModel):
    rule_id: str = Field(..., description="ID de la regla en Kibana")
    name: str = Field(..., description="Nombre de la regla")
    severity: Optional[str] = Field(None, description="Severidad inferida de las acciones")
    notification_channel: Optional[str] = Field(None, description="Canal de notificación más restrictivo inferido de las acciones")
    apis_alertadas: List[str] = Field(default_factory=list, description="APIs a las que aplica la regla (extraídas del KQL o termField)")
    message: Optional[str] = Field(None, description="Mensaje descriptivo de la regla (annotations.message)")
