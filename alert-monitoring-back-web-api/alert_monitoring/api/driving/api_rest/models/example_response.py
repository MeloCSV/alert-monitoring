from datetime import datetime
from typing import Optional
from typing_extensions import Annotated

from pydantic import BaseModel, StringConstraints, Field

from alert_monitoring.api.domain.models.identification_types_enum import IdentificationTypesEnum


class ExampleResponse(BaseModel):
    id: Optional[int] = None
    name: str
    description: Annotated[str, StringConstraints(min_length=5, max_length=30)]
    creation_time: datetime
    identification_type: IdentificationTypesEnum
    identification: Annotated[str, StringConstraints(pattern=r'^[0-9][0-9]{7}[A-Z]|[A-Z][0-9]{7}[A-Z]$')]
    number_of_days_in_week: Annotated[int, Field(ge=1, le=7)]
