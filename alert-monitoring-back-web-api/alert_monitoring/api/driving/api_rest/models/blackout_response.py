from pydantic import BaseModel
from typing import List


class BlackoutMatcherResponse(BaseModel):
    name: str
    value: str
    isRegex: bool
    isEqual: bool


class BlackoutResponse(BaseModel):
    id: str
    cluster: str
    matchers: List[BlackoutMatcherResponse]
    starts_at: str
    ends_at: str
    created_by: str
    comment: str
