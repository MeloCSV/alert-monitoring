import logging
from typing import List

from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.driven.atlassian_assets_repository.clients.atlassian_assets_http_client import (
    AtlassianAssetsHttpClient,
    ATTR_CSW_CODE,
    ATTR_PLATFORM,
)
from alert_monitoring.api.driven.atlassian_assets_repository.config.atlassian_assets_settings import load_atlassian_assets_config

logger = logging.getLogger(__name__)


class AtlassianAssetsAdapter:

    def __init__(self) -> None:
        self.client = AtlassianAssetsHttpClient()

    def fetch_catalog_apps(self) -> List[CatalogApp]:
        config = load_atlassian_assets_config()
        if config is None:
            return []

        raw_objects = self.client.fetch_catalog_objects(config)
        apps: List[CatalogApp] = []

        for obj in raw_objects:
            object_id = obj.get("id")
            name = obj.get("label") or obj.get("name")

            if not object_id or not name:
                logger.warning("Objeto del catálogo sin id o nombre, ignorado: %s", obj)
                continue

            attributes = obj.get("attributes", [])
            if not self.client.extract_attribute(attributes, ATTR_PLATFORM):
                logger.debug("Aplicación '%s' sin plataforma (legacy), ignorada.", name)
                continue

            csw_code = self.client.extract_attribute(attributes, ATTR_CSW_CODE)

            apps.append(CatalogApp(
                object_id=str(object_id),
                name=name,
                csw_code=csw_code,
            ))

        return apps
