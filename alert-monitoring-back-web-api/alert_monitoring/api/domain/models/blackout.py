from pydantic import BaseModel
from typing import List


class BlackoutMatcher(BaseModel):
    name: str
    value: str
    isRegex: bool = False
    isEqual: bool = True


class Blackout(BaseModel):
    id: str
    cluster: str
    matchers: List[BlackoutMatcher]
    starts_at: str
    ends_at: str
    created_by: str
    comment: str
