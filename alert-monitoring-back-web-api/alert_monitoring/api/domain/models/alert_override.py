from pydantic import BaseModel, Field


class AlertOverride(BaseModel):
    alert_name: str = Field(..., description="Nombre de la alerta Por Defecto")
    microservice: str = Field(..., description="Microservicio para el que se evalúa la alerta")
    is_disabled: bool = Field(
        ...,
        description="True si la alerta Por Defecto está deshabilitada para este microservicio "
                    "(excluida en default y no incluida en default-criticas)"
    )
