import time
from concurrent.futures import ThreadPoolExecutor, Future
from logging import Logger
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driving.catalog_app_api_service_port import CatalogAppApiServicePort
from alert_monitoring.api.application.ports.driving.catalog_service_port import CatalogServicePort
from alert_monitoring.api.application.ports.driving.alert_api_service_port import AlertApiServicePort


router = APIRouter()

_ERROR_500 = {500: {'model': str}}


def _run(fn) -> Dict[str, Any]:
    try:
        return {"synced": fn()}
    except Exception as e:
        return {"error": str(e)}


@router.post('/sync/global', tags=['sync'], status_code=200, responses=_ERROR_500)
def sync_global(
    catalog_service: CatalogServicePort = Depends(Injector.instance(CatalogServicePort)),
    catalog_app_api_service: CatalogAppApiServicePort = Depends(Injector.instance(CatalogAppApiServicePort)),
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    alert_api_service: AlertApiServicePort = Depends(Injector.instance(AlertApiServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info("sync_global started")
    start = time.monotonic()
    results: Dict[str, Any] = {}

    catalog_result = _run(catalog_service.sync_catalog)
    results["catalog"] = catalog_result
    if "error" in catalog_result:
        logger.error(f"sync_global aborted: catalog failed — {catalog_result['error']}")
        results["duration_ms"] = int((time.monotonic() - start) * 1000)
        return JSONResponse(status_code=500, content=results)

    catalog_api_result = _run(catalog_app_api_service.sync_catalog_app_api)
    results["catalog_api"] = catalog_api_result
    if "error" in catalog_api_result:
        logger.error(f"sync_global aborted: catalog_api failed — {catalog_api_result['error']}")
        results["duration_ms"] = int((time.monotonic() - start) * 1000)
        return JSONResponse(status_code=500, content=results)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures: Dict[str, Future] = {
            "alerts_prometheus": executor.submit(_run, alert_service.sync_prometheus_alerts),
            "alerts_elastic": executor.submit(_run, alert_service.sync_elastic_alerts),
            "alert_api": executor.submit(_run, alert_api_service.sync_alert_apis),
        }
    results.update({name: future.result() for name, future in futures.items()})

    results["duration_ms"] = int((time.monotonic() - start) * 1000)
    logger.info(f"sync_global finished in {results['duration_ms']}ms")
    return JSONResponse(status_code=200, content=results)
