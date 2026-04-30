from typing import Optional, List
from pydantic import BaseModel

class AlertResponse(BaseModel):
    name: str
    description: str
    source_tool: str
    severity: str
    condition: str
    environments: List[str]
    microservice: Optional[str] = None
    solution: Optional[str] = None
    notification_channel: Optional[str] = None
    confidence_level: float