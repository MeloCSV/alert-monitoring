from typing import List, Optional
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter

class GetAllAlertsUseCase:
    def __init__(self, repository: AlertRepositoryPort):
        self.repository = repository

    def execute(self, filters: Optional[AlertFilter] = None) -> List[Alert]:
        return self.repository.get_all(filters)