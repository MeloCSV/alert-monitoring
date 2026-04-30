import os
from pathlib import Path

import pytest
from typing import List
from datetime import datetime

from alert_monitoring.api.application.use_cases.example_service_use_case import ExampleServiceUseCase
from alert_monitoring.api.domain.models.example import Example
from alert_monitoring.api.driven.postgres_repository.adapters.example_repository_adapter import ExampleRepositoryAdapter
from alert_monitoring.api.application.exceptions.example_not_found import ExampleNotFoundException
from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n


class TestExampleServiceUseCase:
    @pytest.fixture(scope='function')
    def set_up(self, mocker):
        set_i18n()

        example_repository_adapter_mock = mocker.MagicMock(spec=ExampleRepositoryAdapter)

        example_repository_adapter_mock.list_all = mocker.MagicMock(return_value=[Example(id=1, name='mocked_name',
                                                                    descrip='mocked_description',
                                                                    creation_time=datetime.now(),
                                                                    identification_type='DNI',
                                                                    identification='12345678A',
                                                                    days=2)])

        example_repository_adapter_mock.find_by_id = mocker.MagicMock(side_effect=lambda id_: Example(id=id_,
                                                                      name='mocked_name',
                                                                      descrip='mocked_description',
                                                                      creation_time=datetime.now(),
                                                                      identification_type='DNI',
                                                                      identification='12345678A',
                                                                      days=2))

        example_repository_adapter_mock.save = mocker.MagicMock(
            side_effect=lambda example: Example(id=1, **example.model_dump(exclude_none=True)))
        example_repository_adapter_mock.update = mocker.MagicMock(
            side_effect=lambda id_, example: Example(id=id_, **example.model_dump(exclude_none=True)))

        example_repository_adapter_mock.delete_by_id.return_value = None

        logger_mock = mocker.MagicMock()

        example_service_use_case = ExampleServiceUseCase(example_repository=example_repository_adapter_mock, logger=logger_mock)

        return example_service_use_case
    
    @pytest.fixture(scope='function')
    def set_up_exception(self, mocker):
        set_i18n()
        translations_path = Path(os.path.dirname(__file__)).parent.parent.parent.parent.parent
        load_translations(os.path.join(translations_path, 'alert_monitoring/api/boot/resources/i18n'))

        example_repository_adapter_mock = mocker.MagicMock(spec=ExampleRepositoryAdapter)

        example_repository_adapter_mock.list_all.side_effect = Exception('Testing')

        example_repository_adapter_mock.find_by_id = mocker.MagicMock(
            side_effect=lambda id_: (_ for _ in ()).throw(ExampleNotFoundException(id_)))
        example_repository_adapter_mock.update = mocker.MagicMock(
            side_effect=lambda id_, example: (_ for _ in ()).throw(ExampleNotFoundException(id_)))
        example_repository_adapter_mock.delete_by_id = mocker.MagicMock(
            side_effect=lambda id_: (_ for _ in ()).throw(ExampleNotFoundException(id_)))

        logger_mock = mocker.MagicMock()

        example_service_use_case = ExampleServiceUseCase(example_repository=example_repository_adapter_mock, logger=logger_mock)

        return example_service_use_case
    
    
    def test_should_get_a_page_of_examples(self, set_up):
        """
        Given OK
        When List all examples
        Then Should return example collection
        """

        example_service_use_case = set_up

        result = example_service_use_case.list_all()

        assert isinstance(result, List)
        for item in result:
            assert isinstance(item, Example)
    
    
    def test_should_get_example_with_id(self, set_up):
        """
        Given Valid id
        When Get example
        Then Should return requested example
        """
        id_ = 24

        example_service_use_case = set_up

        result = example_service_use_case.get(id_)

        assert isinstance(result, Example)
    
    
    def test_should_raise_an_exception_if_the_example_to_get_does_not_exist(self, set_up_exception):
        """
        Given Invalid id
        When Get example
        Then Should raise ExampleNotFoundError
        """
        id_ = 24

        example_service_use_case = set_up_exception

        with pytest.raises(ExampleNotFoundException) as exc_info:
            example_service_use_case.get(id_)

        assert exc_info.value.error_code == '00404'
        assert exc_info.value.message == f'No existe ningún ejemplo con el id [{id_}]'
    
    
    def test_should_create_example_with_valid_input(self, set_up):
        """
        Given Valid example
        When Create example
        Then Should return created example
        """

        example_service_use_case = set_up

        example = Example(name='mocked_name', descrip='mocked_description', creation_time=datetime.now(),
                          identification_type='DNI', identification='12345678A', days=2)

        result = example_service_use_case.create(example)

        assert isinstance(result, Example)
        assert result.name == example.name
        assert result.descrip == example.descrip
        assert result.creation_time == example.creation_time
        assert result.identification_type == example.identification_type
        assert result.identification == example.identification
        assert result.days == example.days

    
    def test_should_update_an_example(self, set_up):
        """
        Given Valid id and example
        When Update example
        Then Should return updated example
        """

        example_service_use_case = set_up

        id_ = 24
        example = Example(name='mocked_name', descrip='mocked_description', creation_time=datetime.now(),
                          identification_type='DNI', identification='12345678A', days=2)

        result = example_service_use_case.update(id_, example)

        assert isinstance(result, Example)
        assert result.name == example.name
        assert result.descrip == example.descrip
        assert result.creation_time == example.creation_time
        assert result.identification_type == example.identification_type
        assert result.identification == example.identification
        assert result.days == example.days

    
    def test_should_raise_an_exception_if_the_example_to_update_does_not_exist(self, set_up_exception):
        """
        Given Invalid id
        When Update example
        Then Should raise ExampleNotFoundError
        """

        example_service_use_case = set_up_exception

        id_ = 24
        example = Example(name='mocked_name', descrip='mocked_description', creation_time=datetime.now(),
                          identification_type='DNI', identification='12345678A', days=2)

        with pytest.raises(ExampleNotFoundException) as exc_info:
            example_service_use_case.update(id_, example)

        assert exc_info.value.error_code == '00404'
        assert exc_info.value.message == f'No existe ningún ejemplo con el id [{id_}]'

    
    def test_should_delete_an_example(self, set_up):
        """
        Given Delete id
        When Get example
        Then Should return None
        """

        example_service_use_case = set_up

        id_ = 1

        assert example_service_use_case.delete(id_) is None

    
    def test_should_raise_an_exception_if_the_example_to_delete_does_not_exist(self, set_up_exception):
        """
        Given Invalid id
        When Delete example
        Then Should raise ExampleNotFoundError
        """
        example_service_use_case = set_up_exception

        id_ = 24

        with pytest.raises(ExampleNotFoundException) as exc_info:
            example_service_use_case.delete(id_)

        assert exc_info.value.error_code == '00404'
        assert exc_info.value.message == f'No existe ningún ejemplo con el id [{id_}]'
