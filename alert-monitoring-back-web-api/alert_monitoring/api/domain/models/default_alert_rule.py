from pydantic import BaseModel, Field
from typing import List, Optional

class DefaultAlertRule(BaseModel):
    name: str = Field(..., description="Nombre técnico de la regla (ej. Default_Service_Status_KO)")
    display_name: str = Field(..., description="Nombre legible para mostrar")
    description: str = Field(..., description="Descripción del problema que detecta")
    severity: str
    condition: str = Field(..., description="Expresión PromQL, usada para cómputo de overrides")
    environments: List[str] = Field(default_factory=list)
    notification_channel: Optional[str] = None
    cluster: str = Field(..., description="Cluster K8S de origen")
