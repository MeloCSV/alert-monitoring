from logging import Logger
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.kibana_rule_service_port import KibanaRuleServicePort
from alert_monitoring.api.driving.api_rest.models.kibana_rule_response import KibanaRuleResponse


router = APIRouter()

_ERROR_500 = {500: {'model': str}}


@router.post('/kibana-rules/sync', tags=['kibana-rules'], status_code=201, responses=_ERROR_500)
def sync_kibana_rules(
    service: KibanaRuleServicePort = Depends(Injector.instance(KibanaRuleServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('sync_kibana_rules')
    saved = service.sync_kibana_rules()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Reglas de Kibana sincronizadas correctamente", "saved": saved},
    )


@router.get('/kibana-rules/apis', tags=['kibana-rules'], response_model=List[str], responses=_ERROR_500)
def get_kibana_rule_apis(
    service: KibanaRuleServicePort = Depends(Injector.instance(KibanaRuleServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('get_kibana_rule_apis')
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(service.get_apis()))


@router.get('/kibana-rules', tags=['kibana-rules'], response_model=List[KibanaRuleResponse], responses=_ERROR_500)
def get_kibana_rules(
    api: Optional[str] = Query(None, description="Filtra las reglas por API (transactionElement.serviceName)"),
    is_global: Optional[bool] = Query(None, description="True para reglas globales, False para reglas asociadas a API"),
    service: KibanaRuleServicePort = Depends(Injector.instance(KibanaRuleServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info(f'get_kibana_rules api={api} is_global={is_global}')
    rules = service.get_rules(api=api, is_global=is_global)
    payload = [KibanaRuleResponse(**r.model_dump()) for r in rules]
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(payload))
