from typing import List

from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_model import CatalogAppDB


class CatalogAppDBMapper:

    def to_db(self, app: CatalogApp) -> CatalogAppDB:
        return CatalogAppDB(
            object_id=app.object_id,
            object_key=app.object_key,
            name=app.name,
            csw_code=app.csw_code,
            platform=app.platform,
        )

    def to_domain(self, app_db: CatalogAppDB) -> CatalogApp:
        return CatalogApp(
            object_id=app_db.object_id,
            object_key=app_db.object_key,
            name=app_db.name,
            csw_code=app_db.csw_code,
            platform=app_db.platform,
        )

    def to_domain_list(self, apps_db: List[CatalogAppDB]) -> List[CatalogApp]:
        return [self.to_domain(a) for a in apps_db]
