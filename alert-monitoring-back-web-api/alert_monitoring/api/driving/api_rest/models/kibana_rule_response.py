from typing import List, Optional

from pydantic import BaseModel


class KibanaRuleResponse(BaseModel):
    rule_id: str
    name: str
    enabled: bool
    tags: List[str]
    schedule_interval: Optional[str]
    severity: Optional[str]
    notification_channels: List[str]
    apis: List[str]
    is_global: bool
    last_execution_date: Optional[str]
    last_execution_status: Optional[str]
    kibana_url: Optional[str]
    kibana_name: Optional[str]
    message: Optional[str]
