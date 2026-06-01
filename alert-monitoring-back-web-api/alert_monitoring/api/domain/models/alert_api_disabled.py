from typing import List

from pydantic import BaseModel, Field


class AlertApiDisabled(BaseModel):
    alert_name: str = Field(..., description="Nombre de la alerta global de API")
    api: str = Field(..., description="API para la que se evalúa la alerta")
    is_disabled: bool = Field(..., description="True si la alerta está completamente deshabilitada para esta API")
    is_partial: bool = Field(default=False, description="True si solo algunos sub-elementos están excluidos")
    excluded_items: List[str] = Field(default_factory=list, description="Sub-elementos excluidos del alertado")
