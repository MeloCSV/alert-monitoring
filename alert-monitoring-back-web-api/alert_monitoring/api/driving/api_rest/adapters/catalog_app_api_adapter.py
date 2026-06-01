from logging import Logger
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.catalog_app_api_service_port import CatalogAppApiServicePort
from alert_monitoring.api.driving.api_rest.models.catalog_app_api_response import CatalogAppApiResponse
from alert_monitoring.api.driving.api_rest.responses import ok_list

router = APIRouter()

_ERROR_500 = {500: {'model': str}}


@router.post('/catalog-api/sync', tags=['catalog-api'], status_code=201, responses=_ERROR_500)
def sync_catalog_app_api(
    service: CatalogAppApiServicePort = Depends(Injector.instance(CatalogAppApiServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info("sync_catalog_app_api")
    synced = service.sync_catalog_app_api()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Catálogo app-api sincronizado correctamente", "synced": synced},
    )


@router.get('/catalog-api', tags=['catalog-api'], response_model=List[CatalogAppApiResponse], responses=_ERROR_500)
def get_catalog_app_api(
    app: Optional[str] = Query(None, description="Filtra por nombre de aplicación CNA (coincidencia parcial)"),
    service: CatalogAppApiServicePort = Depends(Injector.instance(CatalogAppApiServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info(f"get_catalog_app_api app={app}")
    items = service.get_all(app=app)
    return ok_list(CatalogAppApiResponse, items)
