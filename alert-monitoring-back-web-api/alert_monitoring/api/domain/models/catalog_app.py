from typing import Optional
from pydantic import BaseModel, Field


class CatalogApp(BaseModel):
    object_id: str = Field(..., description="ID del objeto en Atlassian Assets")
    object_key: str = Field(..., description="Clave del objeto (ej. CAT-49713)")
    name: str = Field(..., description="Nombre de la aplicación")
    csw_code: Optional[str] = Field(None, description="Código CSW de la aplicación")
    platform: Optional[str] = Field(None, description="Plataforma tecnológica (ej. GLKE, Openshift)")
