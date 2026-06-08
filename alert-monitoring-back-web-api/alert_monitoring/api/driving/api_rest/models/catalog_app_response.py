from typing import Optional
from pydantic import BaseModel


class CatalogAppResponse(BaseModel):
    object_id: str
    name: str
    csw_code: Optional[str] = None
