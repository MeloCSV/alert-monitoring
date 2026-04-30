from typing import Union, List
from logging import Logger

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, JSONResponse



from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from alert_monitoring.api.driving.api_rest.models.example_request import ExampleRequest
from alert_monitoring.api.driving.api_rest.models.example_response import ExampleResponse
from alert_monitoring.api.driving.api_rest.mappers.example_dto_mapper import ExampleDTOMapper
from alert_monitoring.api.application.ports.driving.use_case_service_port import UseCaseServicePort


from alert_monitoring.api.domain.models.example import Example


router = APIRouter()


@router.get('/examples', tags=['examples'], response_model=List[ExampleResponse],
            responses={
                500: {'model': str}
            })
def get_example_collection(example_service: UseCaseServicePort[Example] = Depends(Injector.instance(UseCaseServicePort[Example])),
                   api_rest_mapper: ExampleDTOMapper = Depends(Injector.instance(ExampleDTOMapper)),
logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger"))) -> JSONResponse:
    """
    Method to retrieve a collection of examples
    """
    logger.info('get_example_collection')
    examples = example_service.list_all()

    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=jsonable_encoder(api_rest_mapper.to_models_decorator(examples)))


@router.post('/examples', tags=['examples'], status_code=201, response_model=ExampleResponse,
             responses={
                 400: {'model': str},
                 500: {'model': str}
             })
def create_example(example_request: ExampleRequest,
                example_service: UseCaseServicePort[Example] = Depends(Injector.instance(UseCaseServicePort[Example])),
                api_rest_mapper: ExampleDTOMapper = Depends(Injector.instance(ExampleDTOMapper))) -> JSONResponse:
    """
    Method to add one example to the data storage
    """
    
    example = api_rest_mapper.from_model_decorator(example_request)
    
    example = example_service.create(example)
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content=jsonable_encoder(api_rest_mapper.to_model_decorator(example)))


@router.get('/examples/{id_}', tags=['examples'], response_model=ExampleResponse,
            responses={
                400: {'model': str},
                404: {'model': str},
                500: {'model': str}
            })
def get_example(id_: int, example_service: UseCaseServicePort[Example] = Depends(Injector.instance(UseCaseServicePort[Example])),
                api_rest_mapper: ExampleDTOMapper = Depends(Injector.instance(ExampleDTOMapper))) -> JSONResponse:
    """
    Method to retrieve one example
    """
    example = example_service.get(id_)
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=jsonable_encoder(api_rest_mapper.to_model_decorator(example)))


@router.put('/examples/{id_}', tags=['examples'], response_model=ExampleResponse,
            responses={
                400: {'model': str},
                404: {'model': str},
                500: {'model': str}
            })
def update_example(id_: int, example_request: ExampleRequest,
                   example_service: UseCaseServicePort[Example] = Depends(Injector.instance(UseCaseServicePort[Example])),
                   api_rest_mapper: ExampleDTOMapper = Depends(Injector.instance(ExampleDTOMapper))) -> JSONResponse:
    """
    Method to update an example
    """
    
    example_update = api_rest_mapper.from_model_decorator(example_request)
    
    example = example_service.update(id_, example_update)

    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=jsonable_encoder(api_rest_mapper.to_model_decorator(example)))


@router.delete('/examples/{id_}', tags=['examples'], response_model=None, status_code=204,
               responses={
                   404: {'model': str},
                   500: {'model': str}
               })
def delete_example(id_: int,
                   example_service: UseCaseServicePort[Example] = Depends(Injector.instance(UseCaseServicePort[Example])))   -> Union[Response, JSONResponse]:
    """
    Method to delete an example
    """
    example_service.delete(id_)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
