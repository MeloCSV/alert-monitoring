from typing import Optional
from pydantic import BaseModel


class CatalogAppResponse(BaseModel):
    object_id: str
    object_key: str
    name: str
    csw_code: Optional[str] = None
    platform: Optional[str] = None
