from datetime import datetime
from typing_extensions import Annotated

from pydantic import BaseModel, StringConstraints, Field

from alert_monitoring.api.domain.models.identification_types_enum import IdentificationTypesEnum


class ExampleRequest(BaseModel):
    name: str
    description: Annotated[str, StringConstraints(min_length=5, max_length=30)]
    creation_time: datetime
    identification_type: IdentificationTypesEnum
    identification: Annotated[str, StringConstraints(pattern=r'^[0-9][0-9]{7}[A-Z]|[A-Z][0-9]{7}[A-Z]$')]
    number_of_days_in_week: Annotated[int, Field(ge=1, le=7)]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Test",
                    "description": "My description",
                    "creation_time": "2024-04-09T14:07:54.698Z",
                    "identification_type": "DNI",
                    "identification": "12345678A",
                    "number_of_days_in_week": 1
                }
            ]
        }
    }
