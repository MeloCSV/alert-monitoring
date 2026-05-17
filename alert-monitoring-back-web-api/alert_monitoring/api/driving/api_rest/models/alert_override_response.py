from typing import List

from pydantic import BaseModel, Field


class AlertOverrideResponse(BaseModel):
    alert_name: str
    solution: str
    is_disabled: bool
    is_partial: bool = False
    excluded_items: List[str] = Field(default_factory=list)
