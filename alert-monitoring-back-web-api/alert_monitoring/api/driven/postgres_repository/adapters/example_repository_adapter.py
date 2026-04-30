from typing import List

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup


from fwkpy_lib_database.synchronous.datasource import DataSourceManager


from alert_monitoring.api.domain.models.example import Example
from alert_monitoring.api.application.ports.driven.database_repository_port import DatabaseRepositoryPort
from alert_monitoring.api.application.exceptions.example_not_found import ExampleNotFoundException
from alert_monitoring.api.driven.postgres_repository.models.example import ExampleMO

from alert_monitoring.api.driven.postgres_repository.mappers.example_mapper import ExampleMapper


class ExampleRepositoryAdapter(DatabaseRepositoryPort[Example]):
    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(self, sqlalchemy_repository: DataSourceManager, postgres_mapper: ExampleMapper, logger:LoggerSetup):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.postgres_mapper = postgres_mapper
        self.logger = logger

    
    def find_by_id(self, id_: int) -> Example:
        self.logger.info('find by id')
        example_mo = self.sqlalchemy_repository.query(ExampleMO).get(id_)
        if example_mo:
            
            return self.postgres_mapper.from_model_decorator(example_mo)
            
        raise ExampleNotFoundException(id_)

    def list_all(self) -> List[Example]:
        examples_mo = self.sqlalchemy_repository.query(ExampleMO).all()
        
        return self.postgres_mapper.from_models_decorator(examples_mo)
        
    def save(self, example: Example) -> Example:
        
        example_mo = self.postgres_mapper.to_model_decorator(example)
        
        self.sqlalchemy_repository.add(example_mo)
        self.sqlalchemy_repository.commit()
        self.sqlalchemy_repository.refresh(example_mo)
        
        return self.postgres_mapper.from_model_decorator(example_mo)
        
    def update(self, id_: int, example: Example) -> Example:
        example_mo = self.sqlalchemy_repository.query(ExampleMO).get(id_)
        if example_mo:
            example_mo.name = example.name
            example_mo.description = example.descrip
            example_mo.creation_time = example.creation_time
            example_mo.identification_type = example.identification_type
            example_mo.identification = example.identification
            example_mo.number_of_days_in_week = example.days

            self.sqlalchemy_repository.add(example_mo)
            self.sqlalchemy_repository.commit()
            self.sqlalchemy_repository.refresh(example_mo)
            
            return self.postgres_mapper.from_model_decorator(example_mo)
            
        raise ExampleNotFoundException(id_)

    def delete_by_id(self, id_: int) -> None:
        example_mo = self.sqlalchemy_repository.query(ExampleMO).get(id_)

        if example_mo:
            self.sqlalchemy_repository.delete(example_mo)
            self.sqlalchemy_repository.commit()
            return

        raise ExampleNotFoundException(id_)        

