"""Tests for loot blueprint."""
import json
import pytest
from unittest.mock import patch, MagicMock

LOOT_TOTALS = {
    'total_rows': 42, 'total_quantity': 198, 'total_value': 850000000.0,
    'unique_items': 17, 'runs_with_loot': 12
}

TOP_ITEMS = [
    {'item_name': 'Intact Armor Nanobot', 'item_category': 'artifacts',
     'total_quantity': 50, 'total_value': 750000000.0, 'avg_price': 15000000.0, 'found_in_runs': 8},
    {'item_name': 'Malfunctioning Hull Section', 'item_category': 'artifacts',
     'total_quantity': 30, 'total_value': 660000000.0, 'avg_price': 22000000.0, 'found_in_runs': 6},
]

CAT_BREAKDOWN = [
    {'item_category': 'artifacts', 'unique_items': 5, 'total_quantity': 80, 'total_value': 700000000.0, 'run_count': 10},
    {'item_category': 'datacores',  'unique_items': 3, 'total_quantity': 60, 'total_value': 100000000.0, 'run_count': 5},
]

BY_TYPE = [
    {'site_type': 'relic', 'total_loot_value': 600000000.0, 'run_count': 8},
    {'site_type': 'data',  'total_loot_value': 250000000.0, 'run_count': 4},
]

MONTHLY = [
    {'month': '2026-01-01', 'loot_value': 200000000.0, 'runs': 3},
    {'month': '2026-02-01', 'loot_value': 310000000.0, 'runs': 5},
    {'month': '2026-03-01', 'loot_value': 340000000.0, 'runs': 4},
]


def _build_loot_db():
    mock_conn = MagicMock()
    mock_cur  = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = LOOT_TOTALS
    mock_cur.fetchall.side_effect = [TOP_ITEMS, CAT_BREAKDOWN, MONTHLY, BY_TYPE]
    return mock_conn


class TestLootRoutes:

    def test_loot_page_returns_200(self, client):
        r = client.get('/loot/')
        assert r.status_code == 200

    def test_loot_page_contains_analysis(self, client):
        r = client.get('/loot/')
        data = r.data.decode()
        assert 'LOOT' in data or 'loot' in data.lower()

    def test_loot_page_contains_stat_cards(self, client):
        r = client.get('/loot/')
        data = r.data.decode()
        assert 'ls-total-value' in data or 'Total Loot Value' in data


class TestLootAPI:

    def test_api_loot_stats_returns_200(self, client):
        mock_conn = _build_loot_db()
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/stats')
        assert r.status_code == 200

    def test_api_loot_stats_structure(self, client):
        mock_conn = _build_loot_db()
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/stats')
        d = json.loads(r.data)
        assert 'totals'      in d
        assert 'top_items'   in d
        assert 'by_category' in d
        assert 'monthly'     in d
        assert 'by_type'     in d

    def test_api_loot_stats_totals(self, client):
        mock_conn = _build_loot_db()
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/stats')
        d = json.loads(r.data)
        assert d['totals']['unique_items'] == 17
        assert d['totals']['runs_with_loot'] == 12

    def test_api_loot_stats_top_items_list(self, client):
        mock_conn = _build_loot_db()
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/stats')
        d = json.loads(r.data)
        assert len(d['top_items']) == 2
        assert d['top_items'][0]['item_name'] == 'Intact Armor Nanobot'

    def test_api_loot_stats_by_category(self, client):
        mock_conn = _build_loot_db()
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/stats')
        d = json.loads(r.data)
        assert len(d['by_category']) == 2
        assert d['by_category'][0]['item_category'] == 'artifacts'

    def test_api_loot_stats_monthly_trend(self, client):
        mock_conn = _build_loot_db()
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/stats')
        d = json.loads(r.data)
        assert len(d['monthly']) == 3

    def test_api_loot_stats_by_type(self, client):
        mock_conn = _build_loot_db()
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/stats')
        d = json.loads(r.data)
        assert len(d['by_type']) == 2
        types = [t['site_type'] for t in d['by_type']]
        assert 'relic' in types
        assert 'data'  in types

    def test_api_loot_stats_empty_db(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None
        mock_cur.fetchall.return_value = []
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/stats')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['top_items'] == []
        assert d['by_category'] == []

    def test_api_loot_items_returns_list(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            {'id': 1, 'run_id': 1, 'item_name': 'Intact Armor Nanobot',
             'item_category': 'artifacts', 'quantity': 5, 'unit_price': 15000000.0,
             'total_price': 75000000.0, 'region_name': 'Vale', 'run_date': '2026-03-27', 'site_type': 'relic'}
        ]
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/items')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert isinstance(d, list)
        assert len(d) == 1

    def test_api_loot_items_filter_by_category(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/items?category=artifacts')
        assert r.status_code == 200

    def test_api_loot_items_empty(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []
        with patch('loot.get_db', return_value=mock_conn):
            r = client.get('/api/loot/items')
        assert r.status_code == 200
        assert json.loads(r.data) == []
