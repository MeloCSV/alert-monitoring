from typing import List

from pydantic import BaseModel, Field


class CatalogAppApi(BaseModel):
    app: str = Field(..., description="Nombre canónico de la aplicación CNA (de catalog_apps)")
    microservice: str = Field(..., description="Nombre completo del microservicio/despliegue")
    apis: List[str] = Field(default_factory=list, description="APIs producidas por este microservicio")
