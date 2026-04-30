from typing import List
from logging import Logger

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.driving.api_rest.models.alert_request import AlertUploadRequest, ElasticUploadRequest
from alert_monitoring.api.driving.api_rest.models.alert_response import AlertResponse
from alert_monitoring.api.driving.api_rest.mappers.alert_dto_mapper import AlertDTOMapper
from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort

router = APIRouter()


@router.post('/alerts/upload', tags=['alerts'], status_code=201,
             responses={
                 400: {'model': str},
                 500: {'model': str}
             })
def upload_yaml(request: AlertUploadRequest,
                alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
                logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger"))) -> JSONResponse:
    """
    Recibe un YAML de Prometheus, lo parsea y guarda las alertas en BD
    """
    logger.info('upload_yaml')
    alert_service.save_alerts(request.yaml_content)
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content={"message": "Alertas guardadas correctamente"})


@router.post('/alerts/upload/elastic', tags=['alerts'], status_code=201,
             responses={
                 400: {'model': str},
                 500: {'model': str}
             })
def upload_elastic_json(request: ElasticUploadRequest,
                alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
                logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger"))) -> JSONResponse:
    """
    Recibe un JSON de Elastic, lo parsea y guarda las alertas en BD
    """
    logger.info('upload_elastic_json')
    alert_service.save_elastic_alerts(request.json_content)
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content={"message": "Alertas de Elastic guardadas correctamente"})


@router.get('/alerts', tags=['alerts'], response_model=List[AlertResponse],
            responses={
                500: {'model': str}
            })
def get_all_alerts(alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
                   api_rest_mapper: AlertDTOMapper = Depends(Injector.instance(AlertDTOMapper)),
                   logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger"))) -> JSONResponse:
    """
    Devuelve todas las alertas guardadas en BD
    """
    logger.info('get_all_alerts')
    alerts = alert_service.get_all_alerts()
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=jsonable_encoder(api_rest_mapper.to_models_decorator(alerts)))