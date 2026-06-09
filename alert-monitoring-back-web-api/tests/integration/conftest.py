import pytest
from sqlalchemy.engine import make_url, URL
from sqlalchemy.orm import Session
from sqlmodel import SQLModel, create_engine
from testcontainers.postgres import PostgresContainer

# Todos los modelos deben importarse antes de create_all para registrarse en el metadata
from alert_monitoring.api.driven.postgres_repository.models.alert_model import AlertDB  # noqa: F401
from alert_monitoring.api.driven.postgres_repository.models.default_alert_model import DefaultAlertDB  # noqa: F401
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_model import CatalogAppDB  # noqa: F401
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_api_model import CatalogAppApiDB  # noqa: F401
from alert_monitoring.api.driven.postgres_repository.models.alert_api_model import AlertApiDB  # noqa: F401
from alert_monitoring.api.driven.postgres_repository.models.default_alert_api_model import DefaultAlertApiDB  # noqa: F401


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_engine(pg_container):
    raw = make_url(pg_container.get_connection_url())
    url = URL.create(
        drivername="postgresql+psycopg",
        username=raw.username,
        password=raw.password,
        host=raw.host,
        port=raw.port,
        database=raw.database,
    )
    engine = create_engine(url)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """
    Cada test recibe una sesión envuelta en una transacción que se revierte al acabar.
    Los session.commit() del código bajo test solo confirman hasta el savepoint,
    no la transacción exterior, por lo que los datos no persisten entre tests.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()
