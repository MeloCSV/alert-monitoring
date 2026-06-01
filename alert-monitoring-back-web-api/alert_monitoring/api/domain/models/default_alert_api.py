from typing import List, Optional

from pydantic import BaseModel, Field


class DefaultAlertApi(BaseModel):
    raw_name: str = Field(..., description="Nombre técnico original de la alerta")
    display_name: str = Field(..., description="Nombre legible para la UI")
    raw_description: Optional[str] = Field(None, description="Descripción técnica original")
    display_description: Optional[str] = Field(None, description="Descripción traducida para la UI")
    severity: Optional[str] = Field(None)
    notification_channel: Optional[str] = Field(None)
    excluded_apis: List[str] = Field(default_factory=list)
