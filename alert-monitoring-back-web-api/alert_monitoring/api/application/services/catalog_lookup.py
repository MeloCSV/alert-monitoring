"""Utilidad compartida para resolver nombres canónicos del catálogo de apps."""
from typing import Dict

from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort


def build_catalog_lookup(catalog_app_repository: CatalogAppRepositoryPort) -> Dict[str, str]:
    """Devuelve un dict ``{nombre_en_minúsculas: nombre_canónico}`` del catálogo de apps."""
    return {app.name.lower(): app.name for app in catalog_app_repository.get_all()}
