import os
from pathlib import Path

import pytest
from typing import List
from datetime import datetime




from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from fwkpy_lib_database.synchronous.datasource import set_db_session_context


from alert_monitoring.api.driven.postgres_repository.models.example import ExampleMO
from alert_monitoring.api.domain.models.example import Example
from alert_monitoring.api.driven.postgres_repository.adapters.example_repository_adapter import ExampleRepositoryAdapter

from alert_monitoring.api.application.exceptions.example_not_found import ExampleNotFoundException
from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n


class TestExampleRepositoryAdapter:

    @pytest.fixture(scope='function')
    def set_up(self, mocker):
        set_i18n()
        set_db_session_context(session_id="test_session")
        translations_path = Path(os.path.dirname(__file__)).parent.parent.parent.parent.parent.parent
        load_translations(
            os.path.join(translations_path, 'alert_monitoring/api/boot/resources/i18n'))
        
        
        
        session_mock = mocker.MagicMock(spec=Session)
        session_mock.commit = mocker.MagicMock(return_value=None)
        session_mock.rollback = mocker.MagicMock(return_value=None)
        session_mock.flush = mocker.MagicMock(return_value=None)
        session_mock.add = mocker.MagicMock(return_value=None)
        session_mock.delete = mocker.MagicMock(return_value=None)
        session_mock.refresh = mocker.MagicMock(return_value=None)

        def query(model):
            query_mock = mocker.MagicMock(spec=Query)

            query_mock.get = mocker.MagicMock(side_effect=lambda id_: None
                                              if id_ == 0
                                              else ExampleMO(id=id_, name='mocked_name',
                                                             description='mocked_description',
                                                             creation_time=datetime.now(), identification_type='DNI',
                                                             identification='12345678A', number_of_days_in_week=2))

            query_mock.all = mocker.MagicMock(return_value=[ExampleMO(id=1, name='mocked_name',
                                                                      description='mocked_description',
                                                                      creation_time=datetime.now(),
                                                                      identification_type='DNI',
                                                                      identification='12345678A',
                                                                      number_of_days_in_week=2)])

            return query_mock

        session_mock.query = query
        
        logger_mock = mocker.MagicMock()

        example_repository_adapter = ExampleRepositoryAdapter(sqlalchemy_repository=session_mock, logger=logger_mock)

        return example_repository_adapter

    
    def test_should_get_example_collection(self, set_up):
        """
        Given OK
        When List all examples
        Then Should return example collection
        """
        example_repository_adapter = set_up

        result = example_repository_adapter.list_all()

        assert isinstance(result, List)
        for item in result:
            assert isinstance(item, Example)

    
    def test_should_get_example(self, set_up):
        """
        Given Valid id
        When Get example
        Then Should return requested example
        """
        id_ = 1
        example_repository_adapter = set_up

        result = example_repository_adapter.find_by_id(id_)

        assert isinstance(result, Example)
        assert result.id == id_
        assert result.name == 'mocked_name'
        assert result.descrip == 'mocked_description'

    
    def test_should_raise_example_not_found_error_on_get(self, set_up):
        """
        Given Invalid id
        When Get example
        Then Should raise ExampleNotFoundError
        """
        id_ = 0
        example_repository_adapter = set_up

        with pytest.raises(ExampleNotFoundException) as exc_info:
            example_repository_adapter.find_by_id(id_)

        assert exc_info.value.error_code == '00404'
        assert exc_info.value.message == f'No existe ningún ejemplo con el id [{id_}]'

    
    def test_should_create_example(self, set_up):
        """
        Given Valid example
        When Create example
        Then Should return created example
        """
        example_repository_adapter = set_up

        example = Example(name='mocked name', descrip='mocked description', creation_time=datetime.now(),
                          identification_type='DNI', identification='12345678A', days=4)

        result = example_repository_adapter.save(example)

        assert result.name == example.name

    
    def test_should_update_example(self, set_up):
        """
        Given Valid id and example
        When Update example
        Then Should return updated example
        """
        id_ = 1
        example_repository_adapter = set_up

        example = Example(id=id_, name='mocked name1', descrip='mocked description', creation_time=datetime.now(),
                          identification_type='DNI', identification='12345678A', days=4)

        result = example_repository_adapter.update(id_, example)

        assert result.name == example.name

    
    def test_should_raise_example_not_found_error_on_update(self, set_up):
        """
        Given Invalid id
        When Update example
        Then Should raise ExampleNotFoundError
        """
        id_ = 0
        example_repository_adapter = set_up

        example = Example(id=id_, name='mocked name', descrip='mocked description', creation_time=datetime.now(),
                          identification_type='DNI', identification='12345678A', days=4)

        with pytest.raises(ExampleNotFoundException) as exc_info:
            example_repository_adapter.update(id_, example)

        assert exc_info.value.error_code == '00404'
        assert exc_info.value.message == f'No existe ningún ejemplo con el id [{id_}]'

    
    def test_should_delete_an_example(self, set_up):
        """
        Given Delete id
        When Get example
        Then Should return None
        """
        id_ = 1
        example_repository_adapter = set_up

        assert example_repository_adapter.delete_by_id(id_) is None

    
    def test_should_raise_example_not_found_error_on_delete(self, set_up):
        """
        Given Invalid id
        When Delete example
        Then Should raise ExampleNotFoundError
        """
        id_ = 0
        example_repository_adapter = set_up

        with pytest.raises(ExampleNotFoundException) as exc_info:
            example_repository_adapter.delete_by_id(id_)

        assert exc_info.value.error_code == '00404'
        assert exc_info.value.message == f'No existe ningún ejemplo con el id [{id_}]'
