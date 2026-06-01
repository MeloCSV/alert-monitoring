import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Resolves to alert-monitoring-back-web-api/resources/catalog_app_api.json
_RESOURCES_PATH = Path(__file__).parents[5] / "resources" / "catalog_app_api.json"


class CatalogAppApiFileAdapter:

    def fetch_entries(self) -> List[dict]:
        if not _RESOURCES_PATH.exists():
            logger.warning("Fichero de correlación app-api no encontrado: %s", _RESOURCES_PATH)
            return []
        with open(_RESOURCES_PATH, encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Leídas %d entradas de %s", len(data), _RESOURCES_PATH)
        return data
