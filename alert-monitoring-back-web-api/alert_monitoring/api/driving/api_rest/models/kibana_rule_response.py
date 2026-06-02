from typing import List, Optional

from pydantic import BaseModel


class AlertApiResponse(BaseModel):
    rule_id: str
    name: str
    tags: List[str]
    severity: Optional[str]
    notification_channel: Optional[str]
    apis_alertadas: List[str]
    message: Optional[str]
