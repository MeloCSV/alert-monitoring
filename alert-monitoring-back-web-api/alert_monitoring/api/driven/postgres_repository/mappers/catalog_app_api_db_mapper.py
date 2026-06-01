from typing import List

from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_api_model import CatalogAppApiDB


class CatalogAppApiDBMapper:

    def to_db(self, item: CatalogAppApi) -> CatalogAppApiDB:
        return CatalogAppApiDB(
            app=item.app,
            microservice=item.microservice,
            apis=item.apis,
        )

    def to_domain(self, db: CatalogAppApiDB) -> CatalogAppApi:
        return CatalogAppApi(
            app=db.app,
            microservice=db.microservice,
            apis=db.apis or [],
        )

    def to_domain_list(self, items: List[CatalogAppApiDB]) -> List[CatalogAppApi]:
        return [self.to_domain(i) for i in items]
