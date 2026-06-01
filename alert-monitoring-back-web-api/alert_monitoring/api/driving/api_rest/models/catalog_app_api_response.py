from typing import List

from pydantic import BaseModel


class CatalogAppApiResponse(BaseModel):
    app: str
    microservice: str
    apis: List[str]
