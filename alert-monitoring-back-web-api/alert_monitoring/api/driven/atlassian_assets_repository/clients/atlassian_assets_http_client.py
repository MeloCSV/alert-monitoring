import base64
import logging
from typing import List

import httpx

from alert_monitoring.api.driven.atlassian_assets_repository.models.atlassian_assets_config import AtlassianAssetsConfig

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0

ATTR_CSW_CODE = "401"
ATTR_PLATFORM = "426"


class AtlassianAssetsHttpClient:

    def fetch_catalog_objects(self, config: AtlassianAssetsConfig) -> List[dict]:
        url = f"{config.base_url.rstrip('/')}/workspace/{config.workspace_id}/v1/object/aql"
        credentials = base64.b64encode(f"{config.email}:{config.token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        body = {"qlQuery": f"objectTypeId = {config.object_type_id}"}

        objects: List[dict] = []
        start_at = 0

        with httpx.Client(verify=config.verify_ssl, timeout=DEFAULT_TIMEOUT) as client:
            while True:
                params = {"startAt": start_at, "maxResults": config.page_size}
                try:
                    response = client.post(url, headers=headers, params=params, json=body)
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    logger.error("Error al consultar Atlassian Assets (startAt=%s): %s", start_at, exc)
                    break

                payload = response.json()
                page = payload.get("values", [])
                if not isinstance(page, list) or not page:
                    break

                objects.extend(page)
                start_at += len(page)

                if len(page) < config.page_size:
                    break

        logger.info("Recuperados %d objetos del catálogo Atlassian Assets", len(objects))
        return objects

    @staticmethod
    def extract_attribute(attributes: List[dict], attribute_id: str) -> str | None:
        for attr in attributes:
            if str(attr.get("objectTypeAttributeId")) == attribute_id:
                values = attr.get("objectAttributeValues", [])
                if values:
                    return values[0].get("displayValue")
        return None
