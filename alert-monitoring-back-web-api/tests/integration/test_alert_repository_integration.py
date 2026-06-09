import pytest
from unittest.mock import MagicMock

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.driven.postgres_repository.adapters.alert_repository import AlertRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.mappers.alert_db_mapper import AlertDBMapper


def _make_alert(**kwargs) -> Alert:
    defaults = dict(
        name="test-alert",
        description="Descripción de prueba",
        source_tool="Prometheus",
        severity="warning",
        chips=[],
        environments=["pro"],
        solution="my-app",
        notification_channel="teams",
    )
    defaults.update(kwargs)
    return Alert(**defaults)


@pytest.mark.integration
class TestAlertRepositoryIntegration:

    @pytest.fixture
    def repo(self, db_session):
        return AlertRepositoryAdapter(
            sqlalchemy_repository=db_session,
            alert_db_mapper=AlertDBMapper(),
            logger=MagicMock(),
        )

    def test_save_and_retrieve_all(self, repo):
        """Guardar dos alertas y recuperarlas sin filtros devuelve las dos."""
        repo.save_all([
            _make_alert(name="alert-1"),
            _make_alert(name="alert-2"),
        ])

        results = repo.get_all()

        assert len(results) == 2
        assert {r.name for r in results} == {"alert-1", "alert-2"}

    def test_save_persists_all_fields(self, repo):
        """Todos los campos opcionales se almacenan y se recuperan correctamente."""
        alert = _make_alert(
            name="full-alert",
            description="Descripción completa",
            source_tool="Elastic",
            severity="critical",
            chips=["ns-prod", "ns-dev"],
            environments=["pro", "pre"],
            microservice="api-gateway",
            solution="my-platform",
            notification_channel="servicenow",
        )

        repo.save_all([alert])
        results = repo.get_all()

        assert len(results) == 1
        saved = results[0]
        assert saved.name == "full-alert"
        assert saved.source_tool == "Elastic"
        assert saved.chips == ["ns-prod", "ns-dev"]
        assert saved.environments == ["pro", "pre"]
        assert saved.microservice == "api-gateway"
        assert saved.solution == "my-platform"
        assert saved.notification_channel == "servicenow"

    def test_filter_by_solution_exact_match(self, repo):
        """El filtro por solution hace coincidencia exacta y no devuelve otras apps."""
        repo.save_all([
            _make_alert(name="alert-a", solution="app-one"),
            _make_alert(name="alert-b", solution="app-two"),
        ])

        results = repo.get_all(AlertFilter(solution="app-one"))

        assert len(results) == 1
        assert results[0].name == "alert-a"

    def test_filter_by_severity(self, repo):
        """El filtro por severity devuelve solo las alertas con esa severidad."""
        repo.save_all([
            _make_alert(name="crit", severity="critical"),
            _make_alert(name="warn", severity="warning"),
            _make_alert(name="principal", severity="principal"),
        ])

        results = repo.get_all(AlertFilter(severity="critical"))

        assert len(results) == 1
        assert results[0].name == "crit"

    def test_filter_by_name_is_case_insensitive_partial_match(self, repo):
        """El filtro por nombre usa ilike, es insensible a mayúsculas y parcial."""
        repo.save_all([
            _make_alert(name="HighCpuUsage"),
            _make_alert(name="LowMemory"),
        ])

        results = repo.get_all(AlertFilter(name="cpu"))

        assert len(results) == 1
        assert results[0].name == "HighCpuUsage"

    def test_filter_by_environments_returns_matching_and_multi_env(self, repo):
        """El filtro por entorno devuelve alertas que incluyan ese entorno en su lista."""
        repo.save_all([
            _make_alert(name="pro-only", environments=["pro"]),
            _make_alert(name="dev-only", environments=["dev"]),
            _make_alert(name="multi-env", environments=["dev", "pro"]),
        ])

        results = repo.get_all(AlertFilter(environments=["pro"]))

        names = {r.name for r in results}
        assert "pro-only" in names
        assert "multi-env" in names
        assert "dev-only" not in names

    def test_delete_by_source_tool_removes_only_that_tool(self, repo):
        """Borrar por source_tool elimina solo las alertas de esa herramienta."""
        repo.save_all([
            _make_alert(name="prom-alert", source_tool="Prometheus"),
            _make_alert(name="elastic-alert", source_tool="Elastic"),
        ])

        repo.delete_by_source_tool("Prometheus")

        results = repo.get_all()
        assert len(results) == 1
        assert results[0].name == "elastic-alert"
        assert results[0].source_tool == "Elastic"

    def test_delete_by_source_tool_with_no_matching_rows_does_nothing(self, repo):
        """Borrar por un source_tool que no existe no elimina nada."""
        repo.save_all([_make_alert(name="elastic-alert", source_tool="Elastic")])

        repo.delete_by_source_tool("Prometheus")

        results = repo.get_all()
        assert len(results) == 1

    def test_get_all_without_filters_returns_everything(self, repo):
        """Sin filtros se devuelven todas las alertas de la tabla."""
        repo.save_all([
            _make_alert(name="a1", solution="app-a", severity="warning"),
            _make_alert(name="a2", solution="app-b", severity="critical"),
            _make_alert(name="a3", solution="app-a", severity="principal"),
        ])

        results = repo.get_all()

        assert len(results) == 3

    def test_filter_by_microservice_partial_match(self, repo):
        """El filtro por microservice usa ilike y es parcial."""
        repo.save_all([
            _make_alert(name="a1", microservice="order-service"),
            _make_alert(name="a2", microservice="payment-service"),
        ])

        results = repo.get_all(AlertFilter(microservice="order"))

        assert len(results) == 1
        assert results[0].name == "a1"
