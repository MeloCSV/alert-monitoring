from typing import List, Optional

from pydantic import BaseModel, Field


class BlackoutMatcher(BaseModel):
    name: str
    value: str
    is_regex: bool = False
    is_equal: bool = True


class Blackout(BaseModel):
    id: str
    matchers: List[BlackoutMatcher] = Field(default_factory=list)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    created_by: Optional[str] = None
    comment: Optional[str] = None
    state: str = "active"
    source: Optional[str] = None
