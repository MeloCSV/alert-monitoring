from typing import List, Optional
from pydantic import BaseModel


class DefaultAlertResponse(BaseModel):
    raw_name: str
    display_name: str
    raw_description: Optional[str]
    display_description: Optional[str]
    severity: Optional[str]
    notification_channel: Optional[str]
    excluded_namespaces: List[str]
    included_namespaces: List[str]
    excluded_jobs: List[str]
