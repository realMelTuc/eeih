"""Tests for regions blueprint."""
import json
import pytest
from unittest.mock import patch, MagicMock

REGION_ROWS = [
    {'region_name': 'Vale of Silent', 'total_runs': 5, 'total_value': 520000000.0,
     'avg_value': 104000000.0, 'best_run': 210000000.0, 'worst_run': 31000000.0,
     'last_run': '2026-03-27', 'relic_count': 4, 'data_count': 1,
     'runs_30d': 3, 'value_30d': 280000000.0},
    {'region_name': 'Deklein', 'total_runs': 3, 'total_value': 240000000.0,
     'avg_value': 80000000.0, 'best_run': 110000000.0, 'worst_run': 45000000.0,
     'last_run': '2026-03-25', 'relic_count': 2, 'data_count': 1,
     'runs_30d': 2, 'value_30d': 190000000.0},
]

REGION_RUNS = [
    {'id': 1, 'site_type': 'relic', 'site_name': 'Cache', 'system_name': 'J1',
     'security_class': 'WH', 'difficulty': 'superior',
     'run_date': '2026-03-27', 'total_loot_value': 210000000.0, 'run_time_seconds': 900},
]


class TestRegionsRoutes:

    def test_regions_page_returns_200(self, client):
        r = client.get('/regions/')
        assert r.status_code == 200

    def test_regions_page_contains_table(self, client):
        r = client.get('/regions/')
        data = r.data.decode()
        assert 'REGIONS' in data or 'region' in data.lower()


class TestRegionsAPI:

    def test_api_regions_stats_returns_list(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = REGION_ROWS
        with patch('regions.get_db', return_value=mock_conn):
            r = client.get('/api/regions/stats')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert isinstance(d, list)
        assert len(d) == 2

    def test_api_regions_stats_empty(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []
        with patch('regions.get_db', return_value=mock_conn):
            r = client.get('/api/regions/stats')
        assert r.status_code == 200
        assert json.loads(r.data) == []

    def test_api_regions_stats_fields(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [REGION_ROWS[0]]
        with patch('regions.get_db', return_value=mock_conn):
            r = client.get('/api/regions/stats')
        d = json.loads(r.data)
        region = d[0]
        assert 'region_name' in region
        assert 'total_runs' in region
        assert 'total_value' in region
        assert 'avg_value' in region
        assert 'best_run' in region

    def test_api_regions_stats_sorted_by_value(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = REGION_ROWS
        with patch('regions.get_db', return_value=mock_conn):
            r = client.get('/api/regions/stats')
        d = json.loads(r.data)
        assert d[0]['region_name'] == 'Vale of Silent'
        assert d[1]['region_name'] == 'Deklein'

    def test_api_region_runs_returns_list(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = REGION_RUNS
        with patch('regions.get_db', return_value=mock_conn):
            r = client.get('/api/regions/Vale%20of%20Silent/runs')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert isinstance(d, list)

    def test_api_region_runs_empty(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []
        with patch('regions.get_db', return_value=mock_conn):
            r = client.get('/api/regions/UnknownRegion/runs')
        assert r.status_code == 200
        assert json.loads(r.data) == []

    def test_api_regions_30d_fields(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = REGION_ROWS
        with patch('regions.get_db', return_value=mock_conn):
            r = client.get('/api/regions/stats')
        d = json.loads(r.data)
        assert 'runs_30d' in d[0]
        assert 'value_30d' in d[0]

    def test_api_regions_relic_data_split(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = REGION_ROWS
        with patch('regions.get_db', return_value=mock_conn):
            r = client.get('/api/regions/stats')
        d = json.loads(r.data)
        assert 'relic_count' in d[0]
        assert 'data_count' in d[0]
