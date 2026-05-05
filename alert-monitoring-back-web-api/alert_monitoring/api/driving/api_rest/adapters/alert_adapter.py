from typing import List, Optional
from logging import Logger

from fastapi import APIRouter, Depends, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.driving.api_rest.models.alert_request import AlertUploadRequest, ElasticUploadRequest
from alert_monitoring.api.driving.api_rest.models.alert_response import AlertResponse
from alert_monitoring.api.driving.api_rest.mappers.alert_dto_mapper import AlertDTOMapper
from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.domain.models.alert_filter import AlertFilter


router = APIRouter()


@router.post('/alerts/upload', tags=['alerts'], status_code=201,
             responses={
                 400: {'model': str},
                 500: {'model': str}
             })
def upload_yaml(request: AlertUploadRequest,
                alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
                logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger"))) -> JSONResponse:
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
    logger.info('upload_elastic_json')
    alert_service.save_elastic_alerts(request.json_content)
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content={"message": "Alertas de Elastic guardadas correctamente"})


@router.get('/alerts', tags=['alerts'], response_model=List[AlertResponse],
            responses={
                500: {'model': str}
            })
def get_all_alerts(name: Optional[str] = Query(None, description="Filtra por nombre (coincidencia parcial)"),
    source_tool: Optional[str] = Query(None, description="Prometheus o Elastic"),
    severity: Optional[str] = Query(None, description="Warning, Critical o Principal"),
    environments: Optional[List[str]] = Query(None, description="Entornos: dev, itg, pre, pro"),
    microservice: Optional[str] = Query(None, description="Filtra por microservicio (coincidencia parcial)"),
    solution: Optional[str] = Query(None, description="Filtra por solución (coincidencia parcial)"),
    alert_type: Optional[str] = Query(None, description="Por Defecto o Ad-hoc"),
    is_overridden: Optional[bool] = Query(None, description="Si la alerta ha sido sustituida"),
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    api_rest_mapper: AlertDTOMapper = Depends(Injector.instance(AlertDTOMapper)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger"))
    ) -> JSONResponse: 
        logger.info('get_all_alerts')
        filters = AlertFilter(
            name=name,
            source_tool=source_tool,
            severity=severity,
            environments=environments,
            microservice=microservice,
            solution=solution,
            alert_type=alert_type,
            is_overridden=is_overridden,
        )
        alerts = alert_service.get_all_alerts(filters)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(api_rest_mapper.to_models_decorator(alerts)))
