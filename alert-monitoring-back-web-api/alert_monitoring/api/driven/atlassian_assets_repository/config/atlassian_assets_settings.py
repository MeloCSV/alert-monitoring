import logging
import os

from alert_monitoring.api.driven.atlassian_assets_repository.models.atlassian_assets_config import AtlassianAssetsConfig

logger = logging.getLogger(__name__)

WORKSPACE_ID_VAR = "ATLASSIAN_ASSETS_WORKSPACE_ID"
BASE_URL_VAR = "ATLASSIAN_ASSETS_BASE_URL"
EMAIL_VAR = "ATLASSIAN_ASSETS_EMAIL"
TOKEN_VAR = "ATLASSIAN_ASSETS_TOKEN"
OBJECT_TYPE_ID_VAR = "ATLASSIAN_ASSETS_OBJECT_TYPE_ID"
PAGE_SIZE_VAR = "ATLASSIAN_ASSETS_PAGE_SIZE"

DEFAULT_BASE_URL = "https://api.atlassian.com/jsm/assets"


def load_atlassian_assets_config() -> AtlassianAssetsConfig | None:
    workspace_id = os.environ.get(WORKSPACE_ID_VAR)
    email = os.environ.get(EMAIL_VAR)
    token = os.environ.get(TOKEN_VAR)
    object_type_id = os.environ.get(OBJECT_TYPE_ID_VAR)

    if not workspace_id or not email or not token or not object_type_id:
        missing = [v for v, val in [
            (WORKSPACE_ID_VAR, workspace_id),
            (EMAIL_VAR, email),
            (TOKEN_VAR, token),
            (OBJECT_TYPE_ID_VAR, object_type_id),
        ] if not val]
        logger.warning("Variables de entorno de Atlassian Assets no definidas: %s; no se sincronizará el catálogo.", missing)
        return None

    return AtlassianAssetsConfig(
        workspace_id=workspace_id,
        base_url=os.environ.get(BASE_URL_VAR, DEFAULT_BASE_URL),
        email=email,
        token=token,
        object_type_id=object_type_id,
        page_size=int(os.environ.get(PAGE_SIZE_VAR, "100")),
    )
