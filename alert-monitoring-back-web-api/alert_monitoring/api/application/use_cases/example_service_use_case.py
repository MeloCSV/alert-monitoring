from typing import List

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup


from alert_monitoring.api.domain.models.example import Example

from alert_monitoring.api.application.ports.driving.use_case_service_port import UseCaseServicePort
from alert_monitoring.api.application.ports.driven.database_repository_port import DatabaseRepositoryPort


class ExampleServiceUseCase(UseCaseServicePort[Example]):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(self, example_repository: DatabaseRepositoryPort[Example], logger: LoggerSetup):
        self.example_repository = example_repository
        self.logger = logger

    def list_all(self) -> List[Example]:
        self.logger.info('List all examples')
        return self.example_repository.list_all()

    def get(self, id_: int) -> Example:
        return self.example_repository.find_by_id(id_)

    def create(self, example: Example) -> Example:
        return self.example_repository.save(example)

    def update(self, id_: int, example: Example) -> Example:
        return self.example_repository.update(id_, example)

    def delete(self, id_: int) -> None:
        self.example_repository.delete_by_id(id_)
