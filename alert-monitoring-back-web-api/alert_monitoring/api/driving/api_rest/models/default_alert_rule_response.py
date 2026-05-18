from typing import Optional, List
from pydantic import BaseModel

class DefaultAlertRuleResponse(BaseModel):
    name: str
    display_name: str
    description: str
    severity: str
    condition: str
    environments: List[str]
    notification_channel: Optional[str] = None
    cluster: str
    solution: Optional[str] = None
