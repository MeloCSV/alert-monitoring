from typing import Optional, List
from pydantic import BaseModel


class AlertResponse(BaseModel):
    name: str
    description: str
    source_tool: str
    severity: str
    environments: List[str]
    microservice: Optional[str] = None
    solution: Optional[str] = None
    notification_channel: Optional[str] = None
    chips: List[str] = []
