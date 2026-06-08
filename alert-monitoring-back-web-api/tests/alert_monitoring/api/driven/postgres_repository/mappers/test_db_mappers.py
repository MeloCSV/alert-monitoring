"""Tests for postgres repository DB mappers (pure Python, no DB required)."""
import pytest

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.domain.models.catalog_app import CatalogApp
from alert_monitoring.api.domain.models.catalog_app_api import CatalogAppApi
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi

from alert_monitoring.api.driven.postgres_repository.mappers.alert_db_mapper import AlertDBMapper
from alert_monitoring.api.driven.postgres_repository.mappers.alert_api_db_mapper import AlertApiDBMapper
from alert_monitoring.api.driven.postgres_repository.mappers.catalog_app_db_mapper import CatalogAppDBMapper
from alert_monitoring.api.driven.postgres_repository.mappers.catalog_app_api_db_mapper import CatalogAppApiDBMapper
from alert_monitoring.api.driven.postgres_repository.mappers.default_alert_db_mapper import DefaultAlertDBMapper
from alert_monitoring.api.driven.postgres_repository.mappers.default_alert_api_db_mapper import DefaultAlertApiDBMapper

from alert_monitoring.api.driven.postgres_repository.models.alert_model import AlertDB
from alert_monitoring.api.driven.postgres_repository.models.alert_api_model import AlertApiDB
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_model import CatalogAppDB
from alert_monitoring.api.driven.postgres_repository.models.catalog_app_api_model import CatalogAppApiDB
from alert_monitoring.api.driven.postgres_repository.models.default_alert_model import DefaultAlertDB
from alert_monitoring.api.driven.postgres_repository.models.default_alert_api_model import DefaultAlertApiDB


# ---------------------------------------------------------------------------
# AlertDBMapper
# ---------------------------------------------------------------------------

class TestAlertDBMapper:
    @pytest.fixture
    def mapper(self):
        return AlertDBMapper()

    def test_to_db_maps_all_fields(self, mapper):
        alert = Alert(name='A', description='D', source_tool='Prometheus', severity='warning',
                      environments=['pro'], microservice='svc', solution='app',
                      notification_channel='Teams', chips=['svc-back'])
        db = mapper.to_db(alert)
        assert db.name == 'A'
        assert db.source_tool == 'Prometheus'
        assert db.severity == 'warning'
        assert db.solution == 'app'
        assert db.chips == ['svc-back']

    def test_to_domain_maps_all_fields(self, mapper):
        db = AlertDB(name='A', description='D', source_tool='Prometheus', severity='warning',
                     environments=['pro'], microservice='svc', solution='app',
                     notification_channel='Teams', chips=['svc-back'])
        alert = mapper.to_domain(db)
        assert alert.name == 'A'
        assert alert.source_tool == 'Prometheus'
        assert alert.solution == 'app'
        assert alert.chips == ['svc-back']

    def test_to_domain_handles_none_chips(self, mapper):
        db = AlertDB(name='A', description='D', source_tool='Prometheus', severity='warning', chips=None)
        alert = mapper.to_domain(db)
        assert alert.chips == []

    def test_to_domain_list_returns_multiple(self, mapper):
        dbs = [
            AlertDB(name='A', description='D', source_tool='P', severity='w'),
            AlertDB(name='B', description='D', source_tool='P', severity='w'),
        ]
        result = mapper.to_domain_list(dbs)
        assert len(result) == 2
        assert result[0].name == 'A'
        assert result[1].name == 'B'


# ---------------------------------------------------------------------------
# AlertApiDBMapper
# ---------------------------------------------------------------------------

class TestAlertApiDBMapper:
    @pytest.fixture
    def mapper(self):
        return AlertApiDBMapper()

    def test_to_db_maps_all_fields(self, mapper):
        rule = AlertApi(rule_id='r1', name='Rule', severity='critical',
                        notification_channel='ServiceNow', apis_alertadas=['api-a'], message='msg')
        db = mapper.to_db(rule)
        assert db.rule_id == 'r1'
        assert db.apis_alertadas == ['api-a']
        assert db.message == 'msg'

    def test_to_domain_maps_all_fields(self, mapper):
        db = AlertApiDB(rule_id='r1', name='Rule', severity='critical',
                        notification_channel='ServiceNow', apis_alertadas=['api-a'], message='msg')
        rule = mapper.to_domain(db)
        assert rule.rule_id == 'r1'
        assert rule.apis_alertadas == ['api-a']

    def test_to_domain_handles_none_apis(self, mapper):
        db = AlertApiDB(rule_id='r1', name='Rule', apis_alertadas=None)
        rule = mapper.to_domain(db)
        assert rule.apis_alertadas == []

    def test_to_domain_list_returns_multiple(self, mapper):
        dbs = [AlertApiDB(rule_id='r1', name='A'), AlertApiDB(rule_id='r2', name='B')]
        result = mapper.to_domain_list(dbs)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# CatalogAppDBMapper
# ---------------------------------------------------------------------------

class TestCatalogAppDBMapper:
    @pytest.fixture
    def mapper(self):
        return CatalogAppDBMapper()

    def test_to_db(self, mapper):
        app = CatalogApp(object_id='oid', name='my-app', csw_code='CSW001')
        db = mapper.to_db(app)
        assert db.object_id == 'oid'
        assert db.name == 'my-app'
        assert db.csw_code == 'CSW001'

    def test_to_domain(self, mapper):
        db = CatalogAppDB(object_id='oid', name='my-app', csw_code='CSW001')
        app = mapper.to_domain(db)
        assert app.object_id == 'oid'
        assert app.name == 'my-app'

    def test_to_domain_list(self, mapper):
        dbs = [CatalogAppDB(object_id='1', name='a'), CatalogAppDB(object_id='2', name='b')]
        result = mapper.to_domain_list(dbs)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# CatalogAppApiDBMapper
# ---------------------------------------------------------------------------

class TestCatalogAppApiDBMapper:
    @pytest.fixture
    def mapper(self):
        return CatalogAppApiDBMapper()

    def test_to_db(self, mapper):
        item = CatalogAppApi(app='my-app', microservice='my-back', apis=['api-a', 'api-b'])
        db = mapper.to_db(item)
        assert db.app == 'my-app'
        assert db.microservice == 'my-back'
        assert db.apis == ['api-a', 'api-b']

    def test_to_domain(self, mapper):
        db = CatalogAppApiDB(app='my-app', microservice='my-back', apis=['api-a'])
        item = mapper.to_domain(db)
        assert item.app == 'my-app'
        assert item.apis == ['api-a']

    def test_to_domain_handles_none_apis(self, mapper):
        db = CatalogAppApiDB(app='a', microservice='b', apis=None)
        item = mapper.to_domain(db)
        assert item.apis == []

    def test_to_domain_list(self, mapper):
        dbs = [CatalogAppApiDB(app='a', microservice='ma', apis=[]),
               CatalogAppApiDB(app='b', microservice='mb', apis=[])]
        result = mapper.to_domain_list(dbs)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# DefaultAlertDBMapper
# ---------------------------------------------------------------------------

class TestDefaultAlertDBMapper:
    @pytest.fixture
    def mapper(self):
        return DefaultAlertDBMapper()

    def test_to_domain(self, mapper):
        db = DefaultAlertDB(raw_name='Default_Status', display_name='Estado',
                            severity='warning', excluded_namespaces=['excl'],
                            included_namespaces=['incl'], excluded_jobs=['job'])
        result = mapper.to_domain(db)
        assert result.raw_name == 'Default_Status'
        assert result.excluded_namespaces == ['excl']
        assert result.included_namespaces == ['incl']
        assert result.excluded_jobs == ['job']

    def test_to_domain_handles_none_lists(self, mapper):
        db = DefaultAlertDB(raw_name='D', display_name='N',
                            excluded_namespaces=None, included_namespaces=None, excluded_jobs=None)
        result = mapper.to_domain(db)
        assert result.excluded_namespaces == []
        assert result.included_namespaces == []
        assert result.excluded_jobs == []

    def test_to_domain_list(self, mapper):
        dbs = [DefaultAlertDB(raw_name='A', display_name='A'),
               DefaultAlertDB(raw_name='B', display_name='B')]
        result = mapper.to_domain_list(dbs)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# DefaultAlertApiDBMapper
# ---------------------------------------------------------------------------

class TestDefaultAlertApiDBMapper:
    @pytest.fixture
    def mapper(self):
        return DefaultAlertApiDBMapper()

    def test_to_domain(self, mapper):
        db = DefaultAlertApiDB(raw_name='Global_Rule', display_name='Rule',
                               severity='critical', notification_channel='ServiceNow',
                               excluded_apis=['api-a'])
        result = mapper.to_domain(db)
        assert result.raw_name == 'Global_Rule'
        assert result.excluded_apis == ['api-a']

    def test_to_domain_handles_none_apis(self, mapper):
        db = DefaultAlertApiDB(raw_name='R', display_name='N', excluded_apis=None)
        result = mapper.to_domain(db)
        assert result.excluded_apis == []

    def test_to_domain_list(self, mapper):
        dbs = [DefaultAlertApiDB(raw_name='A', display_name='A'),
               DefaultAlertApiDB(raw_name='B', display_name='B')]
        result = mapper.to_domain_list(dbs)
        assert len(result) == 2
