from typing import Optional

from pydantic import BaseModel


class KibanaConfig(BaseModel):
    name: str
    base_url: str
    api_key: str
    space_id: Optional[str] = None
    verify_ssl: bool = True
    per_page: int = 100
    max_pages: int = 100
