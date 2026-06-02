from typing import List, Optional
from logging import Logger

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.catalog_service_port import CatalogServicePort
from alert_monitoring.api.driving.api_rest.models.catalog_app_response import CatalogAppResponse
from alert_monitoring.api.driving.api_rest.responses import ok_list


router = APIRouter()

_ERROR_500 = {500: {'model': str}}


@router.post('/catalog/sync', tags=['catalog'], status_code=201, responses=_ERROR_500)
def sync_catalog(
    catalog_service: CatalogServicePort = Depends(Injector.instance(CatalogServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info("sync_catalog")
    synced = catalog_service.sync_catalog()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Catálogo de aplicaciones sincronizado correctamente", "synced": synced},
    )


@router.get('/catalog', tags=['catalog'], response_model=List[CatalogAppResponse], responses=_ERROR_500)
def get_catalog_apps(
    name: Optional[str] = Query(None, description="Filtra por nombre de aplicación (coincidencia parcial)"),
    catalog_service: CatalogServicePort = Depends(Injector.instance(CatalogServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info("get_catalog_apps")
    apps = catalog_service.get_all_catalog_apps(name=name)
    return ok_list(CatalogAppResponse, apps)
