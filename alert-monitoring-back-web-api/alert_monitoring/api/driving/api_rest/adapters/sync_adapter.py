import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from logging import Logger
from typing import Any, Dict

from fastapi import Depends
from fwkpy_lib_fastapi.public.observability import TracingRouter
from fastapi.responses import JSONResponse
from opentelemetry.metrics import get_meter_provider

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import set_db_session_context, clean_session_context

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driving.catalog_app_api_service_port import CatalogAppApiServicePort
from alert_monitoring.api.application.ports.driving.catalog_service_port import CatalogServicePort
from alert_monitoring.api.application.ports.driving.alert_api_service_port import AlertApiServicePort


router = TracingRouter()

_meter = get_meter_provider().get_meter("alert-monitoring-back-web-api")
_sync_duration = _meter.create_histogram(
    name="alert_monitoring.sync.duration",
    description="Duration of sync operations in milliseconds",
    unit="ms",
)
_sync_calls = _meter.create_counter(
    name="alert_monitoring.sync.calls",
    description="Total sync operation calls",
    unit="{call}",
)
_sync_errors = _meter.create_counter(
    name="alert_monitoring.sync.errors",
    description="Total failed sync sub-operations",
    unit="{error}",
)

_ERROR_500 = {500: {'model': str}}


def _run(fn) -> Dict[str, Any]:
    try:
        return {"synced": fn()}
    except Exception as e:
        return {"error": str(e)}


def _run_isolated(fn) -> Dict[str, Any]:
    token = set_db_session_context(session_id=str(uuid.uuid4()))
    try:
        return _run(fn)
    finally:
        clean_session_context(token=token)


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

    _sync_calls.add(1, {"operation": "global"})

    catalog_result = _run(catalog_service.sync_catalog)
    results["catalog"] = catalog_result
    if "error" in catalog_result:
        logger.error(f"sync_global aborted: catalog failed — {catalog_result['error']}")
        duration_ms = int((time.monotonic() - start) * 1000)
        results["duration_ms"] = duration_ms
        _sync_errors.add(1, {"operation": "catalog"})
        _sync_duration.record(duration_ms, {"operation": "global", "status": "error"})
        return JSONResponse(status_code=500, content=results)

    catalog_api_result = _run(catalog_app_api_service.sync_catalog_app_api)
    results["catalog_api"] = catalog_api_result
    if "error" in catalog_api_result:
        logger.error(f"sync_global aborted: catalog_api failed — {catalog_api_result['error']}")
        duration_ms = int((time.monotonic() - start) * 1000)
        results["duration_ms"] = duration_ms
        _sync_errors.add(1, {"operation": "catalog_api"})
        _sync_duration.record(duration_ms, {"operation": "global", "status": "error"})
        return JSONResponse(status_code=500, content=results)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures: Dict[str, Future] = {
            "alerts_prometheus": executor.submit(_run_isolated, alert_service.sync_prometheus_alerts),
            "alerts_elastic": executor.submit(_run_isolated, alert_service.sync_elastic_alerts),
            "alert_api": executor.submit(_run_isolated, alert_api_service.sync_alert_apis),
        }
    results.update({name: future.result() for name, future in futures.items()})

    for op in ["alerts_prometheus", "alerts_elastic", "alert_api"]:
        if "error" in results.get(op, {}):
            _sync_errors.add(1, {"operation": op})

    duration_ms = int((time.monotonic() - start) * 1000)
    results["duration_ms"] = duration_ms
    _sync_duration.record(duration_ms, {"operation": "global", "status": "success"})
    logger.info(f"sync_global finished in {duration_ms}ms")
    return JSONResponse(status_code=200, content=results)
