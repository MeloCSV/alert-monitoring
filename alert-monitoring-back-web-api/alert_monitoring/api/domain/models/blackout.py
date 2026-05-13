import re
from typing import List, Optional

from pydantic import BaseModel, Field


class BlackoutMatcher(BaseModel):
    name: str
    value: str
    is_regex: bool = False
    is_equal: bool = True

    def matches(self, label_value: Optional[str]) -> bool:
        if label_value is None:
            return False
        if self.is_regex:
            try:
                pattern = re.compile(f"^(?:{self.value})$")
            except re.error:
                return False
            hit = bool(pattern.match(label_value))
        else:
            hit = self.value == label_value
        return hit if self.is_equal else not hit


class Blackout(BaseModel):
    id: str
    matchers: List[BlackoutMatcher] = Field(default_factory=list)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    created_by: Optional[str] = None
    comment: Optional[str] = None
    state: str = "active"
