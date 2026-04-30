from typing import List
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort

class SaveAlertsUseCase:
    def __init__(self, repository: AlertRepositoryPort):
        self.repository = repository

    def execute(self, alerts: List[Alert]) -> None:
        self.repository.save_all(alerts)