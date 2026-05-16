from typing import Optional

from pydantic import BaseModel


class AlertManagerConfig(BaseModel):
    name: str
    url: str
    token: Optional[str] = None
    verify_ssl: bool = True
    host_header: Optional[str] = None
    sni_hostname: Optional[str] = None
