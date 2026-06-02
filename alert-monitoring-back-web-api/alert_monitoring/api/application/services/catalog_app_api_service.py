from collections import defaultdict
from typing import Dict, List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driven.catalog_app_api_repository_port import CatalogAppApiRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.ports.driving.catalog_app_api_service_port import CatalogAppApiServicePort
from alert_monitoring.api.application.services.catalog_lookup import build_catalog_lookup
from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi
from alert_monitoring.api.driven.file_repository.adapters.catalog_app_api_file_adapter import CatalogAppApiFileAdapter


class CatalogAppApiService(CatalogAppApiServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        catalog_app_api_repository: CatalogAppApiRepositoryPort,
        catalog_app_repository: CatalogAppRepositoryPort,
        logger: LoggerSetup,
    ):
        self.repository = catalog_app_api_repository
        self.catalog_app_repository = catalog_app_repository
        self.file_adapter = CatalogAppApiFileAdapter()
        self.logger = logger

    def sync_catalog_app_api(self) -> int:
        self.logger.info("sync_catalog_app_api")
        entries = self.file_adapter.fetch_entries()
        catalog_lookup = self._build_catalog_lookup()
        items = self._process_entries(entries, catalog_lookup)
        self.repository.replace_all(items)
        self.logger.info(f"Sincronizados {len(items)} microservicios CNA con sus APIs")
        return len(items)

    def get_all(self, app: Optional[str] = None) -> List[CatalogAppApi]:
        self.logger.info(f"get_all app={app}")
        return self.repository.get_all(app=app)

    def _build_catalog_lookup(self) -> Dict[str, str]:
        return build_catalog_lookup(self.catalog_app_repository)

    def _process_entries(self, entries: List[dict], catalog_lookup: Dict[str, str]) -> List[CatalogAppApi]:
        """Agrupa las entradas por microservicio y filtra solo apps CNA."""
        micro_to_apis: dict[str, list[str]] = defaultdict(list)
        for entry in entries:
            child = entry.get("child", "").strip()
            parent = entry.get("parent", "").strip()
            if child and parent:
                micro_to_apis[child].append(parent)

        result: List[CatalogAppApi] = []
        for microservice, apis in micro_to_apis.items():
            canonical_app = self._resolve_app(microservice, catalog_lookup)
            if canonical_app:
                result.append(CatalogAppApi(
                    app=canonical_app,
                    microservice=microservice,
                    apis=sorted(set(apis)),
                ))
            else:
                self.logger.debug("Microservicio '%s' no pertenece a ninguna app CNA, ignorado", microservice)

        return result

    @staticmethod
    def _resolve_app(microservice: str, catalog_lookup: Dict[str, str]) -> Optional[str]:
        """Extrae el prefijo del microservicio y lo busca en el catálogo de apps."""
        prefix = microservice.split("-")[0].lower()
        return catalog_lookup.get(prefix)
