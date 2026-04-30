import pytest

from datetime import datetime
from typing import List

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

class TestDatabaseRepositoryPort:

    @pytest.mark.parametrize(
        "method_name, method_args",
        [
            ("find_by_id", (1,)),
            ("list_all", ()),
            ("save", (example,)),
            ("update", (1, example,)),
            ("delete_by_id", (1,))
        ]
    )
    def test_cannot_instantiate_subclass_without_implementing_all_methods(self, method_name, method_args):
        from alert_monitoring.api.application.ports.driven.database_repository_port import DatabaseRepositoryPort

        class FakeClass(DatabaseRepositoryPort[Example]):
            def find_by_id(self, id_: int) -> Example:
                return super().find_by_id(id_)

            def list_all(self) -> List[Example]:
                return super().list_all()

            def save(self, example: Example) -> Example:
                return super().save(example)

            def update(self, id_: int, example: Example) -> Example:
                return super().update(id_, example)

            def delete_by_id(self, id_: int) -> None:
                return super().delete_by_id(id_)

        fake_class = FakeClass()
        with pytest.raises(NotImplementedError):
            abstract_method = getattr(fake_class, method_name)
            abstract_method(*method_args)