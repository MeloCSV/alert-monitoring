from typing import List


from fwkpy_lib_core.synchronous.mappers.decorators import mapping


from alert_monitoring.api.driven.postgres_repository.models.example import ExampleMO
from alert_monitoring.api.domain.models.example import Example



class ExampleMapper:

    def from_model_adhoc(self, example_mo: ExampleMO) -> Example:
        return Example(id=example_mo.id,
                       name=example_mo.name,
                       descrip=example_mo.description,
                       creation_time=example_mo.creation_time,
                       identification_type=example_mo.identification_type,
                       identification=example_mo.identification,
                       days=example_mo.number_of_days_in_week)

    @mapping([{'source': 'description', 'target': 'descrip'},
              {'source': 'number_of_days_in_week.real.numerator', 'target': 'days'}])
    def from_model_decorator(self, example_mo: ExampleMO) -> Example:
        # All the logic is in the decorator
        pass

    def from_models_adhoc(self, examples_mo: List[ExampleMO]) -> List[Example]:
        return [Example(id=example_mo.id,
                        name=example_mo.name,
                        descrip=example_mo.description,
                        creation_time=example_mo.creation_time,
                        identification_type=example_mo.identification_type,
                        identification=example_mo.identification,
                        days=example_mo.number_of_days_in_week)
                for example_mo in examples_mo]

    @mapping([{'source': 'description', 'target': 'descrip'},
              {'source': 'number_of_days_in_week', 'target': 'days'}])
    def from_models_decorator(self, examples_mo: List[ExampleMO]) -> List[Example]:
        # All the logic is in the decorator
        pass

    def to_model_adhoc(self, example: Example) -> ExampleMO:
        return ExampleMO(name=example.name,
                         description=example.descrip,
                         creation_time=example.creation_time,
                         identification_type=example.identification_type,
                         identification=example.identification,
                         number_of_days_in_week=example.days)

    @mapping([{'source': 'descrip', 'target': 'description'},
              {'source': 'days', 'target': 'number_of_days_in_week'}])
    def to_model_decorator(self, example: Example) -> ExampleMO:
        # All the logic is in the decorator
        pass
