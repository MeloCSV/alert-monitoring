import pytest
from unittest.mock import MagicMock

from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.driven.postgres_repository.adapters.default_alert_repository import DefaultAlertRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.mappers.default_alert_db_mapper import DefaultAlertDBMapper


def _make_default_alert(**kwargs) -> DefaultAlert:
    defaults = dict(
        raw_name="HighCpuUsage",
        display_name="Alto uso de CPU",
        raw_description="CPU above {{ $value }}%",
        display_description="El uso de CPU supera el umbral configurado.",
        severity="critical",
        notification_channel="teams",
        excluded_namespaces=[],
        included_namespaces=[],
        excluded_jobs=[],
    )
    defaults.update(kwargs)
    return DefaultAlert(**defaults)


@pytest.mark.integration
class TestDefaultAlertRepositoryIntegration:

    @pytest.fixture
    def repo(self, db_session):
        return DefaultAlertRepositoryAdapter(
            sqlalchemy_repository=db_session,
            default_alert_db_mapper=DefaultAlertDBMapper(),
            logger=MagicMock(),
        )

    def test_upsert_inserts_new_default_alert(self, repo):
        """Una alerta nueva se inserta correctamente en la tabla."""
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A")])

        results = repo.get_all()

        assert len(results) == 1
        assert results[0].raw_name == "Alert_A"

    def test_upsert_updates_owned_fields_on_second_call(self, repo):
        """Los campos propios de Prometheus (raw_description, excluded_*) se actualizan."""
        repo.upsert_batch([_make_default_alert(
            raw_name="Alert_A",
            raw_description="old description",
            excluded_namespaces=[],
            excluded_jobs=[],
        )])
        repo.upsert_batch([_make_default_alert(
            raw_name="Alert_A",
            raw_description="new description",
            excluded_namespaces=["ns-excluded"],
            excluded_jobs=["job-a"],
        )])

        results = repo.get_all()

        assert len(results) == 1
        assert results[0].raw_description == "new description"
        assert results[0].excluded_namespaces == ["ns-excluded"]
        assert results[0].excluded_jobs == ["job-a"]

    def test_upsert_preserves_display_description_once_set(self, repo):
        """La display_description no se sobreescribe si ya tiene valor: las traducciones manuales son intocables."""
        repo.upsert_batch([_make_default_alert(
            raw_name="Alert_A",
            display_description="Traducción manual del equipo",
        )])
        repo.upsert_batch([_make_default_alert(
            raw_name="Alert_A",
            display_description="Descripción nueva del pipeline",
        )])

        results = repo.get_all()

        assert results[0].display_description == "Traducción manual del equipo"

    def test_upsert_fills_display_description_when_previously_null(self, repo):
        """Si display_description era null, el siguiente upsert sí puede rellenarlo."""
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A", display_description=None)])
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A", display_description="Primera descripción")])

        results = repo.get_all()

        assert results[0].display_description == "Primera descripción"

    def test_upsert_updates_severity_when_provided(self, repo):
        """La severidad se actualiza si llega con valor en el nuevo upsert."""
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A", severity="warning")])
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A", severity="critical")])

        results = repo.get_all()

        assert results[0].severity == "critical"

    def test_upsert_does_not_overwrite_severity_when_none(self, repo):
        """Si el nuevo upsert no trae severidad, la existente se preserva."""
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A", severity="warning")])
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A", severity=None)])

        results = repo.get_all()

        assert results[0].severity == "warning"

    def test_upsert_batch_inserts_multiple_alerts(self, repo):
        """Un batch con varias alertas nuevas las inserta todas."""
        repo.upsert_batch([
            _make_default_alert(raw_name="Alert_A"),
            _make_default_alert(raw_name="Alert_B"),
            _make_default_alert(raw_name="Alert_C"),
        ])

        results = repo.get_all()

        assert len(results) == 3
        assert {r.raw_name for r in results} == {"Alert_A", "Alert_B", "Alert_C"}

    def test_get_all_returns_results_ordered_by_id(self, repo):
        """Los resultados se ordenan por id de inserción."""
        repo.upsert_batch([
            _make_default_alert(raw_name="Alert_Z"),
            _make_default_alert(raw_name="Alert_A"),
        ])

        results = repo.get_all()

        assert results[0].raw_name == "Alert_Z"
        assert results[1].raw_name == "Alert_A"

    def test_upsert_does_not_create_duplicates(self, repo):
        """Llamar al upsert dos veces con el mismo raw_name no duplica la fila."""
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A")])
        repo.upsert_batch([_make_default_alert(raw_name="Alert_A")])

        results = repo.get_all()

        assert len(results) == 1
