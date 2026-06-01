from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AlertFilter(BaseModel):
    name: Optional[str] = Field(None, description="Filtro por nombre (coincidencia parcial, case-insensitive)")
    source_tool: Optional[Literal["Prometheus", "Elastic"]] = Field( None, description="Herramienta origen de la alerta" )
    severity: Optional[Literal["warning", "critical", "principal"]] = Field( None, description="Nivel de severidad" )
    environments: Optional[List[Literal["dev", "itg", "pre", "pro"]]] = Field(None, description="Entornos donde aplica la alerta")
    microservice: Optional[str] = Field(None, description="Filtro por microservicio (coincidencia parcial)")
    solution: Optional[str] = Field(None, description="PI fabricado (coincidencia parcial)")
