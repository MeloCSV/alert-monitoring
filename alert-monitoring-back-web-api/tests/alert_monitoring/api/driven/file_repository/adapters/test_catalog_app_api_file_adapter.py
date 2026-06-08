import json
from unittest.mock import patch, mock_open

from alert_monitoring.api.driven.file_repository.adapters.catalog_app_api_file_adapter import (
    CatalogAppApiFileAdapter,
    _RESOURCES_PATH,
)


class TestCatalogAppApiFileAdapter:

    def test_returns_empty_list_when_file_not_found(self):
        with patch.object(_RESOURCES_PATH.__class__, 'exists', return_value=False):
            adapter = CatalogAppApiFileAdapter()
            with patch(
                'alert_monitoring.api.driven.file_repository.adapters.catalog_app_api_file_adapter._RESOURCES_PATH'
            ) as mock_path:
                mock_path.exists.return_value = False
                result = adapter.fetch_entries()
        assert result == []

    def test_returns_data_from_json_file(self):
        entries = [{"child": "my-back", "parent": "my-api"}]
        mock_data = json.dumps(entries)
        with patch(
            'alert_monitoring.api.driven.file_repository.adapters.catalog_app_api_file_adapter._RESOURCES_PATH'
        ) as mock_path:
            mock_path.exists.return_value = True
            with patch('builtins.open', mock_open(read_data=mock_data)):
                adapter = CatalogAppApiFileAdapter()
                result = adapter.fetch_entries()
        assert result == entries

    def test_returns_empty_list_when_resource_path_missing(self):
        with patch(
            'alert_monitoring.api.driven.file_repository.adapters.catalog_app_api_file_adapter._RESOURCES_PATH'
        ) as mock_path:
            mock_path.exists.return_value = False
            adapter = CatalogAppApiFileAdapter()
            result = adapter.fetch_entries()
        assert result == []
