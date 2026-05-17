from typing import List

from pydantic import BaseModel, Field


class AlertOverride(BaseModel):
    alert_name: str = Field(..., description="Nombre de la alerta Por Defecto")
    solution: str = Field(..., description="Aplicación para la que se evalúa la alerta")
    is_disabled: bool = Field(
        ...,
        description="True si el namespace entero está excluido en default y no re-incluido en default-criticas"
    )
    is_partial: bool = Field(
        default=False,
        description="True si solo algunos sub-namespaces o jobs de la aplicación están excluidos"
    )
    excluded_items: List[str] = Field(
        default_factory=list,
        description="Jobs o namespaces concretos de la aplicación excluidos del alarmado por defecto"
    )
