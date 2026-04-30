from datetime import datetime
from typing import List

import pytest

from alert_monitoring.api.application.ports.driving.use_case_service_port import UseCaseServicePort
from alert_monitoring.api.domain.models.example import Example

example = Example(id=1,
                  name='mocked_name',
                  descrip='mocked_description',
                  creation_time=datetime.strptime(
                      '2024-04-09T14:07:54.698000',
                      '%Y-%m-%dT%H:%M:%S.%f'),
                  identification_type='DNI',
                  identification='12345678A',
                  days=2)

class TestUseCaseServicePort:

    @pytest.mark.parametrize(
        "method_name, method_args",
        [
            ("get", (1,)),
            ("list_all", ()),
            ("create", (example,)),
            ("update", (1, example,)),
            ("delete", (1,))
        ]
    )
    def test_cannot_instantiate_subclass_without_implementing_all_methods(self, method_name, method_args):
        class FakeClass(UseCaseServicePort[Example]):
            def get(self, id_: int) -> Example:
                return super().get(id_)

            def list_all(self) -> List[Example]:
                return super().list_all()

            def create(self, example: Example) -> Example:
                return super().create(example)

            def update(self, id_: int, example: Example) -> Example:
                return super().update(id_, example)

            def delete(self, id_: int) -> None:
                return super().delete(id_)

        fake_class = FakeClass()
        with pytest.raises(NotImplementedError):
            abstract_method = getattr(fake_class, method_name)
            abstract_method(*method_args)