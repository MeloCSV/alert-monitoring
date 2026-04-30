from typing import List

from alert_monitoring.api.driving.api_rest.models.example_request import ExampleRequest
from alert_monitoring.api.driving.api_rest.models.example_response import ExampleResponse
from alert_monitoring.api.domain.models.example import Example

from fwkpy_lib_core.synchronous.mappers.decorators import mapping



class ExampleDTOMapper:

    def from_model_adhoc(self, example_request: ExampleRequest) -> Example:
        return Example(name=example_request.name,
                       descrip=example_request.description,
                       creation_time=example_request.creation_time,
                       identification_type=example_request.identification_type,
                       identification=example_request.identification,
                       days=example_request.number_of_days_in_week)

    @mapping([{'source': 'description', 'target': 'descrip'},
              {'source': 'number_of_days_in_week', 'target': 'days'}])
    def from_model_decorator(self, example_request: ExampleRequest) -> Example:
        # All the logic is in the decorator
        pass

    def to_model_adhoc(self, example: Example) -> ExampleResponse:
        return ExampleResponse(id=example.id,
                               name=example.name,
                               description=example.descrip,
                               creation_time=example.creation_time,
                               identification_type=example.identification_type,
                               identification=example.identification,
                               number_of_days_in_week=example.days)

    @mapping([{'source': 'descrip', 'target': 'description'},
              {'source': 'days', 'target': 'number_of_days_in_week'}])
    def to_model_decorator(self, example: Example) -> ExampleResponse:
        # All the logic is in the decorator
        pass

    def to_models_adhoc(self, examples: List[Example]) -> List[ExampleResponse]:
        return [ExampleResponse(id=example.id,
                                name=example.name,
                                description=example.descrip,
                                creation_time=example.creation_time,
                                identification_type=example.identification_type,
                                identification=example.identification,
                                number_of_days_in_week=example.days)
                for example in examples]

    @mapping([{'source': 'descrip', 'target': 'description'},
              {'source': 'days', 'target': 'number_of_days_in_week'}])
    def to_models_decorator(self, examples: List[Example]) -> List[ExampleResponse]:
        # All the logic is in the decorator
        pass
