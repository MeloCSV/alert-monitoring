from pydantic import BaseModel, Field


class AlertOverride(BaseModel):
    alert_name: str = Field(..., description="Nombre de la alerta Por Defecto")
    microservice: str = Field(..., description="Microservicio para el que se evalúa la alerta")
    is_disabled: bool = Field(
        ...,
        description="True si todo el namespace está excluido en default y no re-incluido en default-criticas"
    )
    is_partial: bool = Field(
        default=False,
        description="True si solo algún job/deployment del microservicio está excluido (alarmado parcial)"
    )
