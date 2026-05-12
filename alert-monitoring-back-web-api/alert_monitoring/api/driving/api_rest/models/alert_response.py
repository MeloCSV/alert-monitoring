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
    alert_type: str = "Ad-hoc"
    is_overridden: bool = False
    excluded_namespaces: List[str] = []
    target_namespaces: List[str] = []
    category: Optional[str] = None