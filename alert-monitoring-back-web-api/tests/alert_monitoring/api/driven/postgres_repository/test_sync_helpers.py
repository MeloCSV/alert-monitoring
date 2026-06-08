"""Tests for sync_helpers — pure logic with a mocked SQLAlchemy session."""
from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock, call

from alert_monitoring.api.driven.postgres_repository.sync_helpers import (
    reconcile_by_key,
    upsert_preserving_display,
)


# ---------------------------------------------------------------------------
# Minimal fake model / item classes for testing
# ---------------------------------------------------------------------------

@dataclass
class _Item:
    key: str
    value: str
    raw_name: str = ""
    display_name: str = ""
    display_description: Optional[str] = None
    severity: Optional[str] = None
    notification_channel: Optional[str] = None


class _Model:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _apply(row: _Model, item: _Item) -> None:
    row.key = item.key
    row.value = item.value


# ---------------------------------------------------------------------------
# reconcile_by_key
# ---------------------------------------------------------------------------

class TestReconcileByKey:
    def _make_session(self, existing_rows):
        session = MagicMock()
        query_result = MagicMock()
        query_result.all.return_value = existing_rows
        session.query.return_value = query_result
        return session

    def test_inserts_new_item_when_none_exist(self):
        session = self._make_session([])
        item = _Item(key='k1', value='v1')

        reconcile_by_key(session, _Model, [item], key_attr='key', apply_fn=_apply)

        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_updates_existing_item_via_apply_fn(self):
        existing = _Model(key='k1', value='old')
        session = self._make_session([existing])
        item = _Item(key='k1', value='new')

        reconcile_by_key(session, _Model, [item], key_attr='key', apply_fn=_apply)

        assert existing.value == 'new'
        session.add.assert_not_called()
        session.commit.assert_called_once()

    def test_deletes_row_not_in_incoming_batch(self):
        stale = _Model(key='stale', value='x')
        session = self._make_session([stale])

        reconcile_by_key(session, _Model, [], key_attr='key', apply_fn=_apply)

        session.delete.assert_called_once_with(stale)
        session.commit.assert_called_once()

    def test_does_not_delete_row_present_in_batch(self):
        existing = _Model(key='k1', value='x')
        session = self._make_session([existing])
        item = _Item(key='k1', value='new')

        reconcile_by_key(session, _Model, [item], key_attr='key', apply_fn=_apply)

        session.delete.assert_not_called()

    def test_inserts_new_and_deletes_stale_in_same_call(self):
        stale = _Model(key='old-key', value='x')
        session = self._make_session([stale])
        new_item = _Item(key='new-key', value='y')

        reconcile_by_key(session, _Model, [new_item], key_attr='key', apply_fn=_apply)

        session.add.assert_called_once()
        session.delete.assert_called_once_with(stale)
        session.commit.assert_called_once()

    def test_empty_batch_deletes_all_existing(self):
        r1 = _Model(key='k1', value='a')
        r2 = _Model(key='k2', value='b')
        session = self._make_session([r1, r2])

        reconcile_by_key(session, _Model, [], key_attr='key', apply_fn=_apply)

        assert session.delete.call_count == 2
        session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# upsert_preserving_display
# ---------------------------------------------------------------------------

@dataclass
class _DisplayItem:
    raw_name: str
    display_name: str
    display_description: Optional[str] = None
    severity: Optional[str] = None
    notification_channel: Optional[str] = None


class _DisplayModel:
    raw_name = None  # class-level attribute needed for model_cls.raw_name in filter()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, 'display_name'):
            self.display_name = None
        if not hasattr(self, 'display_description'):
            self.display_description = None
        if not hasattr(self, 'severity'):
            self.severity = None
        if not hasattr(self, 'notification_channel'):
            self.notification_channel = None


def _owned_fields(item: _DisplayItem) -> dict:
    return {}


class TestUpsertPreservingDisplay:
    def _make_session(self, existing=None):
        session = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = existing
        session.query.return_value.filter.return_value = filter_mock
        return session

    def test_inserts_when_no_existing_row(self):
        session = self._make_session(existing=None)
        item = _DisplayItem(raw_name='Alert_X', display_name='Alert X', severity='warning')

        upsert_preserving_display(session, _DisplayModel, [item], owned_fields=_owned_fields)

        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_updates_severity_when_existing_and_new_severity(self):
        existing = _DisplayModel(
            raw_name='Alert_X', display_name='Alert X',
            severity='warning', notification_channel=None
        )
        session = self._make_session(existing=existing)
        item = _DisplayItem(raw_name='Alert_X', display_name='Alert X', severity='critical')

        upsert_preserving_display(session, _DisplayModel, [item], owned_fields=_owned_fields)

        assert existing.severity == 'critical'
        session.commit.assert_called_once()

    def test_does_not_overwrite_severity_when_none_incoming(self):
        existing = _DisplayModel(
            raw_name='Alert_X', display_name='Alert X', severity='warning'
        )
        session = self._make_session(existing=existing)
        item = _DisplayItem(raw_name='Alert_X', display_name='Alert X', severity=None)

        upsert_preserving_display(session, _DisplayModel, [item], owned_fields=_owned_fields)

        assert existing.severity == 'warning'

    def test_fills_display_description_only_when_null(self):
        existing = _DisplayModel(
            raw_name='Alert_X', display_name='Alert X',
            display_description=None, severity=None, notification_channel=None
        )
        session = self._make_session(existing=existing)
        item = _DisplayItem(
            raw_name='Alert_X', display_name='Alert X',
            display_description='New desc'
        )

        upsert_preserving_display(session, _DisplayModel, [item], owned_fields=_owned_fields)

        assert existing.display_description == 'New desc'

    def test_does_not_overwrite_existing_display_description(self):
        existing = _DisplayModel(
            raw_name='Alert_X', display_name='Alert X',
            display_description='Existing desc', severity=None, notification_channel=None
        )
        session = self._make_session(existing=existing)
        item = _DisplayItem(
            raw_name='Alert_X', display_name='Alert X',
            display_description='New desc'
        )

        upsert_preserving_display(session, _DisplayModel, [item], owned_fields=_owned_fields)

        assert existing.display_description == 'Existing desc'

    def test_sets_display_name_from_raw_when_display_is_none(self):
        existing = _DisplayModel(
            raw_name='Alert_X', display_name=None,
            display_description=None, severity=None, notification_channel=None
        )
        session = self._make_session(existing=existing)
        item = _DisplayItem(raw_name='Alert_X', display_name='')

        upsert_preserving_display(session, _DisplayModel, [item], owned_fields=_owned_fields)

        assert existing.display_name == 'Alert_X'

    def test_processes_multiple_items(self):
        session = self._make_session(existing=None)
        items = [
            _DisplayItem(raw_name='A', display_name='A'),
            _DisplayItem(raw_name='B', display_name='B'),
        ]

        upsert_preserving_display(session, _DisplayModel, items, owned_fields=_owned_fields)

        assert session.add.call_count == 2
        session.commit.assert_called_once()
