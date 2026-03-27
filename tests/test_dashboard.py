"""Tests for dashboard blueprint."""
import json
import pytest
from unittest.mock import patch, MagicMock


def _make_stats_db(stats, regions, runs, trend, sec_breakdown):
    """Build a mock DB that returns the right rows for each successive fetchone/fetchall call."""
    mock_conn = MagicMock()
    mock_cur  = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    fetchone_seq  = [stats, regions]
    fetchall_seq  = [runs, trend, sec_breakdown]
    fetchone_iter = iter(fetchone_seq)
    fetchall_iter = iter(fetchall_seq)

    mock_cur.fetchone.side_effect = lambda: next(fetchone_iter, None)
    mock_cur.fetchall.side_effect = lambda: next(fetchall_iter, [])
    return mock_conn


class TestDashboardRoutes:

    def test_dashboard_page_returns_200(self, client):
        r = client.get('/dashboard/')
        assert r.status_code == 200

    def test_dashboard_contains_dashboard_text(self, client):
        r = client.get('/dashboard/')
        assert b'DASHBOARD' in r.data or b'dashboard' in r.data.lower()

    def test_dashboard_partial_contains_stat_cards(self, client):
        r = client.get('/dashboard/')
        data = r.data.decode()
        assert 'Total Runs' in data or 'total_runs' in data.lower() or 's-total' in data

    def test_api_health(self, client):
        r = client.get('/api/health')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['status'] == 'ok'
        assert d['app'] == 'EEIH'

    def test_api_debug(self, client):
        r = client.get('/api/debug')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['app'] == 'EEIH'

    def test_index_returns_landing(self, client):
        r = client.get('/')
        assert r.status_code == 200
        assert b'EEIH' in r.data

    def test_app_route_returns_shell(self, client):
        r = client.get('/app')
        assert r.status_code == 200
        assert b'shell' in r.data.lower() or b'EEIH' in r.data


class TestDashboardAPI:

    def test_api_stats_returns_json(self, client):
        stats = {
            'total_runs': 10, 'total_value': 500000000.0,
            'avg_value': 50000000.0, 'best_run_value': 210000000.0,
            'relic_runs': 7, 'data_runs': 3,
            'runs_this_week': 2, 'value_this_week': 85000000.0
        }
        top_region = {'region_name': 'Vale of Silent', 'total_value': 500000000.0, 'run_count': 10}
        runs = [{'id': 1, 'site_type': 'relic', 'site_name': 'Cache', 'region_name': 'Vale',
                 'system_name': 'J1', 'security_class': 'WH', 'difficulty': 'superior',
                 'run_date': '2026-03-27', 'total_loot_value': 210000000.0, 'run_time_seconds': 900}]
        trend = [{'week_start': '2026-03-21', 'runs': 2, 'total_value': 150000000.0}]
        sec = [{'security_class': 'WH', 'runs': 5, 'total_value': 400000000.0}]
        mock_db = _make_stats_db(stats, top_region, runs, trend, sec)

        with patch('dashboard.get_db', return_value=mock_db):
            r = client.get('/api/dashboard/stats')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert 'total_runs' in d
        assert 'recent_runs' in d
        assert 'weekly_trend' in d

    def test_api_stats_total_runs(self, client):
        stats = {'total_runs': 42, 'total_value': 0, 'avg_value': 0,
                 'best_run_value': 0, 'relic_runs': 0, 'data_runs': 0,
                 'runs_this_week': 0, 'value_this_week': 0}
        mock_db = _make_stats_db(stats, None, [], [], [])
        with patch('dashboard.get_db', return_value=mock_db):
            r = client.get('/api/dashboard/stats')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['total_runs'] == 42

    def test_api_stats_no_top_region(self, client):
        stats = {'total_runs': 0, 'total_value': 0, 'avg_value': 0,
                 'best_run_value': 0, 'relic_runs': 0, 'data_runs': 0,
                 'runs_this_week': 0, 'value_this_week': 0}
        mock_db = _make_stats_db(stats, None, [], [], [])
        with patch('dashboard.get_db', return_value=mock_db):
            r = client.get('/api/dashboard/stats')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['top_region'] is None

    def test_api_stats_weekly_trend_list(self, client):
        stats = {'total_runs': 5, 'total_value': 100000000.0, 'avg_value': 20000000.0,
                 'best_run_value': 50000000.0, 'relic_runs': 3, 'data_runs': 2,
                 'runs_this_week': 1, 'value_this_week': 50000000.0}
        trend = [
            {'week_start': '2026-03-14', 'runs': 1, 'total_value': 50000000.0},
            {'week_start': '2026-03-21', 'runs': 4, 'total_value': 50000000.0},
        ]
        mock_db = _make_stats_db(stats, None, [], trend, [])
        with patch('dashboard.get_db', return_value=mock_db):
            r = client.get('/api/dashboard/stats')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert len(d['weekly_trend']) == 2

    def test_api_stats_security_breakdown(self, client):
        stats = {'total_runs': 5, 'total_value': 0, 'avg_value': 0,
                 'best_run_value': 0, 'relic_runs': 0, 'data_runs': 0,
                 'runs_this_week': 0, 'value_this_week': 0}
        sec = [
            {'security_class': 'NS', 'runs': 3, 'total_value': 200000000.0},
            {'security_class': 'WH', 'runs': 2, 'total_value': 150000000.0},
        ]
        mock_db = _make_stats_db(stats, None, [], [], sec)
        with patch('dashboard.get_db', return_value=mock_db):
            r = client.get('/api/dashboard/stats')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert len(d.get('by_security', [])) == 2
