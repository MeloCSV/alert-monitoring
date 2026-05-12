from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Alert(BaseModel):
    name: str = Field(..., description="Nombre de la alerta")
    description: str = Field(..., description="Descripción de la alerta")
    source_tool: Optional[str] = Field(None, description="Herramienta origen: Prometheus o Elastic")
    severity: str = Field(..., description="Nivel de severidad (Critical, Warning, etc.)")
    condition: str = Field(..., description="La consulta o condición que dispara la alerta")
    environments: Optional[List[str]] = Field(default_factory=list, description="Entornos: LAB, PRE, PRO")

    origin_link: Optional[str] = Field(None, description="Enlace directo a la definición")

    # Campos que pueden ser deducibles o inferidos
    microservice: Optional[str] = Field(None, description="Microservicio al que pertenece")
    solution: Optional[str] = Field(None, description="PI frabricado")
    notification_channel: Optional[str] = Field(None, description="Canal o destino de notificación")
    confidence_level: float = Field(0.0, ge=0.0, le=1.0, description="Nivel de confianza del mapeo (0.0 a 1.0)")

    alert_type: Literal["Por Defecto", "Ad-hoc"] = Field(
        default="Ad-hoc",
        description="Indica si es un alertado por defecto o Ad-hoc"
    )
    is_overridden: bool = Field(
        default=False,
        description="True si esta alerta 'Por Defecto' ha sido deshabilitada/sustituida por una versión Ad-hoc"
    )
    excluded_namespaces: List[str] = Field(
        default_factory=list,
        description="Patrones de namespaces (regex) excluidos en la expresión (namespace!~). Útil para alertas Por Defecto: si el namespace de una aplicación coincide, esa alerta está excepcionada para ella."
    )
    target_namespaces: List[str] = Field(
        default_factory=list,
        description="Patrones de namespaces (regex) a los que aplica la alerta (namespace=~). En defaults críticos indica el ámbito; en ad-hoc identifica los namespaces de la app."
    )
    category: Optional[str] = Field(
        None,
        description="Categoría funcional inferida (e.g. Service_Status_KO). Permite detectar si una alerta Por Defecto está machacada por otra Ad-hoc de la misma categoría."
    )
