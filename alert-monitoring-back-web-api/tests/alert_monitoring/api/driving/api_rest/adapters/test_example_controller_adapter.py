import os
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import patch



from fastapi.testclient import TestClient

from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n
from fwkpy_lib_database.synchronous.middlewares import add_session_middleware

from alert_monitoring.api.application.use_cases.example_service_use_case import ExampleServiceUseCase
from alert_monitoring.api.domain.models.example import Example
from alert_monitoring.api.application.exceptions.example_not_found import ExampleNotFoundException
# Needed for the injection
from alert_monitoring.api.driven.postgres_repository.adapters.example_repository_adapter import ExampleRepositoryAdapter # noqa
from fwkpy_lib_fastapi import FastAPIBuilder

class TestExampleControllerAdapter:

    @classmethod
    def setup_class(cls):
        cls.app = FastAPIBuilder()
        add_session_middleware(cls.app)
        set_i18n()
        cls.client = TestClient(cls.app)
        translations_path = Path(os.path.dirname(__file__)).parent.parent.parent.parent.parent.parent
        load_translations(
            os.path.join(translations_path, 'alert_monitoring/api/boot/resources/i18n'))

    @patch.object(ExampleServiceUseCase, ExampleServiceUseCase.list_all.__name__)
    def test_should_get_example_collection(self, mock_get_collection):
        """
        Given Valid request
        When Get examples collection
        Then Should return a collection of examples and status 200
        """
        mock_get_collection.return_value = [Example(id=1, name='mocked_name',
                                                    descrip='mocked_description',
                                                    creation_time=datetime.now(),
                                                    identification_type='DNI',
                                                    identification='12345678A',
                                                    days=2)]

        response = self.client.get('/examples')

        assert response.status_code == 200
        assert isinstance(response.json(), List)
        assert response.headers.get('content-type') == 'application/json'

    @patch.object(ExampleServiceUseCase, ExampleServiceUseCase.create.__name__)
    def test_should_add_example(self, mock_create):
        """
        Given Valid request
        When Create example
        Then Should return the created example and status 201
        """
        mock_create.return_value = Example(id=1, name='mocked_name',
                                           descrip='mocked_description',
                                           creation_time=datetime.strptime(
                                               '2024-04-09T14:07:54.698000',
                                               '%Y-%m-%dT%H:%M:%S.%f'),
                                           identification_type='DNI',
                                           identification='12345678A',
                                           days=2)

        payload = {'name': 'mocked_name', 'description': 'mocked_description',
                   'creation_time': '2024-04-09T14:07:54.698000', 'identification_type': 'DNI',
                   'identification': '12345678A', 'number_of_days_in_week': 2}

        response = self.client.post('/examples', json=payload)

        assert response.status_code == 201
        for key in payload.keys():
            assert response.json()[key] == payload[key]
        assert response.headers.get('content-type') == 'application/json'

    def test_should_return_a_bad_request_status_code_when_uncaught_error_is_raised_on_create(self):
        """
        Given Unreceived field in request
        When Create example
        Then Should return bad request and status 400
        """
        payload = {'description': 'mocked_description', 'creation_time': '2024-04-09T14:07:54.698000',
                   'identification_type': 'DNI', 'identification': '12345678A', 'number_of_days_in_week': 2}

        response = self.client.post('/examples', json=payload)

        assert response.status_code == 400
        assert response.json()['error_resource']['code'] == '0400'
        assert response.json()['error_resource']['description'] == 'Error al validar la petición'
        assert response.headers.get('content-type') == 'application/json'

    @patch.object(ExampleServiceUseCase, ExampleServiceUseCase.get.__name__)
    def test_should_get_example(self, mock_get):
        """
        Given Valid id
        When Get example
        Then Should return the requested example and status 200
        """
        mock_get.side_effect = lambda id_: Example(id=id_,
                                                   name='mocked_name',
                                                   descrip='mocked_description',
                                                   creation_time=datetime.now(),
                                                   identification_type='DNI',
                                                   identification='12345678A',
                                                   days=2)
        id_ = 1

        response = self.client.get(f'/examples/{id_}')

        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/json'

    @patch.object(ExampleServiceUseCase, ExampleServiceUseCase.get.__name__)
    def test_should_return_a_not_found_status_code_when_the_example_does_not_exist(self, mock_get):
        """
        Given Invalid id
        When Get example
        Then Should return ExampleDoesntExistError and status 404
        """
        mock_get.side_effect = lambda id_: (_ for _ in ()).throw(ExampleNotFoundException(id_))
        id_ = 1

        response = self.client.get(f'/examples/{id_}')

        assert response.status_code == 500
        assert response.json()['error_resource']['code'] == '00404'
        assert response.json()['error_resource']['description'] == f'No existe ningún ejemplo con el id [{id_}]'
        assert response.headers.get('content-type') == 'application/json'

    @patch.object(ExampleServiceUseCase, ExampleServiceUseCase.update.__name__)
    def test_should_update_example_by_its_id(self, mock_update):
        """
        Given Valid request and id
        When Update example
        Then Should return the updated example and status 200
        """

        mock_update.side_effect = lambda id_, example: Example(id=id_,
                                                               name='mocked_name',
                                                               descrip='mocked_description',
                                                               creation_time=datetime.strptime(
                                                                   '2024-04-09T14:07:54.698000',
                                                                   '%Y-%m-%dT%H:%M:%S.%f'),
                                                               identification_type='DNI',
                                                               identification='12345678A',
                                                               days=2)

        id_ = 1
        payload = {'name': 'mocked_name', 'description': 'mocked_description',
                   'creation_time': '2024-04-09T14:07:54.698000', 'identification_type': 'DNI',
                   'identification': '12345678A', 'number_of_days_in_week': 2}

        response = self.client.put(f'/examples/{id_}', json=payload)

        assert response.status_code == 200
        for key in payload.keys():
            assert response.json()[key] == payload[key]
        assert response.headers.get('content-type') == 'application/json'

    def test_should_return_a_bad_request_status_code_when_uncaught_error_is_raised_on_update(self):
        """
        Given Unreceived field in request
        When Update example
        Then Should return bad request and status 400
        """
        id_ = 1
        payload = {'description': 'mocked_description', 'creation_time': '2024-04-09T14:07:54.698000',
                   'identification_type': 'DNI', 'identification': '12345678A', 'number_of_days_in_week': 2}

        response = self.client.put(f'/examples/{id_}', json=payload)

        assert response.status_code == 400
        assert response.json()['error_resource']['code'] == '0400'
        assert response.json()['error_resource']['description'] == 'Error al validar la petición'
        assert response.headers.get('content-type') == 'application/json'

    @patch.object(ExampleServiceUseCase, ExampleServiceUseCase.update.__name__)
    def test_should_return_a_not_found_status_when_the_example_to_update_does_not_exist(self, mock_update):
        """
        Given Invalid id
        When Update example
        Then Should return ExampleDoesntExistError and status 404
        """
        mock_update.side_effect = lambda id_, example: (_ for _ in ()).throw(ExampleNotFoundException(id_))
        id_ = 1

        payload = {'name': 'mocked_name', 'description': 'mocked_description',
                   'creation_time': '2024-04-09T14:07:54.698000', 'identification_type': 'DNI',
                   'identification': '12345678A', 'number_of_days_in_week': 2}

        response = self.client.put(f'/examples/{id_}', json=payload)

        assert response.status_code == 500
        assert response.json()['error_resource']['code'] == '00404'
        assert response.json()['error_resource']['description'] == f'No existe ningún ejemplo con el id [{id_}]'
        assert response.headers.get('content-type') == 'application/json'

    @patch.object(ExampleServiceUseCase, ExampleServiceUseCase.delete.__name__)
    def test_should_delete_example_by_its_id(self, mock_delete):
        """
        Given Valid id
        When Delete example
        Then Should return no content and status 204
        """
        mock_delete.return_value = None
        id_ = 1

        response = self.client.delete(f'/examples/{id_}')

        assert response.status_code == 204

    @patch.object(ExampleServiceUseCase, ExampleServiceUseCase.delete.__name__)
    def test_should_return_a_not_found_status_when_the_example_to_delete_does_not_exist(self, mock_delete):
        """
        Given Invalid id
        When Delete example
        Then Should return ExampleDoesntExistError and status 404
        """
        mock_delete.side_effect = lambda id_: (_ for _ in ()).throw(ExampleNotFoundException(id_))
        id_ = 1

        response = self.client.delete(f'/examples/{id_}')

        assert response.status_code == 500
        assert response.json()['error_resource']['code'] == '00404'
        assert response.json()['error_resource']['description'] == f'No existe ningún ejemplo con el id [{id_}]'
        assert response.headers.get('content-type') == 'application/json'
