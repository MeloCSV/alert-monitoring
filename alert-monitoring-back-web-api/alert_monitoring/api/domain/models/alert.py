from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Alert(BaseModel):
    name: str = Field(..., description="Nombre de la alerta")
    description: str = Field(..., description="Descripción de la alerta")
    source_tool: Optional[str] = Field(None, description="Herramienta origen: Prometheus o Elastic")
    severity: str = Field(..., description="Nivel de severidad (Critical, Warning, etc.)")
    condition: str = Field(..., description="La consulta o condición que dispara la alerta")
    environments: Optional[List[str]] = Field(default_factory=list, description="Entornos leídos de la label 'environment'")

    origin_link: Optional[str] = Field(None, description="Enlace directo a la definición")

    microservice: Optional[str] = Field(None, description="Microservicio (label 'namespace')")
    solution: Optional[str] = Field(None, description="PI fabricado (label 'solucion')")
    notification_channel: Optional[str] = Field(None, description="Canal de notificación (label 'canal')")

    alert_type: Literal["Por Defecto", "Ad-hoc"] = Field(
        default="Ad-hoc",
        description="'Por Defecto' si la regla tiene la label alertype=default; 'Ad-hoc' en caso contrario."
    )
    excluded_namespaces: List[str] = Field(
        default_factory=list,
        description="Patrones de namespaces excepcionados (namespace!~ en la expresión). Si el namespace de la app encaja, la default queda excepcionada para ella."
    )
