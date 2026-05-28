from typing import List, Optional

from pydantic import BaseModel


class BlackoutMatcherResponse(BaseModel):
    name: str
    value: str
    is_regex: bool = False
    is_equal: bool = True


class BlackoutResponse(BaseModel):
    id: str
    matchers: List[BlackoutMatcherResponse]
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    created_by: Optional[str] = None
    comment: Optional[str] = None
    source: Optional[str] = None
