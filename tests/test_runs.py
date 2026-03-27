"""Tests for runs blueprint."""
import json
import pytest
from unittest.mock import patch, MagicMock, call


def _mock_db_seq(fetchone_vals=None, fetchall_vals=None):
    mock_conn = MagicMock()
    mock_cur  = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    if fetchone_vals:
        mock_cur.fetchone.side_effect = iter(fetchone_vals)
    if fetchall_vals:
        mock_cur.fetchall.side_effect = iter(fetchall_vals)
    return mock_conn, mock_cur


SAMPLE_RUN = {
    'id': 1, 'site_type': 'relic', 'site_name': 'Superior Sleeper Cache',
    'region_name': 'Vale of Silent', 'system_name': 'J123456',
    'security_class': 'WH', 'difficulty': 'superior',
    'run_date': '2026-03-27', 'total_loot_value': 142000000.0,
    'run_time_seconds': 900, 'notes': None,
    'created_at': '2026-03-27T10:00:00', 'loot_count': 2
}

SAMPLE_LOOT = [
    {'id': 1, 'run_id': 1, 'item_name': 'Intact Armor Nanobot',
     'item_category': 'artifacts', 'quantity': 5, 'unit_price': 15000000.0, 'total_price': 75000000.0},
    {'id': 2, 'run_id': 1, 'item_name': 'Malfunctioning Hull Section',
     'item_category': 'artifacts', 'quantity': 3, 'unit_price': 22000000.0, 'total_price': 66000000.0},
]


class TestRunsRoutes:

    def test_runs_page_returns_200(self, client):
        r = client.get('/runs/')
        assert r.status_code == 200

    def test_runs_page_contains_filter_bar(self, client):
        r = client.get('/runs/')
        data = r.data.decode()
        assert 'filter' in data.lower() or 'ALL RUNS' in data

    def test_new_run_page_returns_200(self, client):
        r = client.get('/runs/new/')
        assert r.status_code == 200

    def test_new_run_page_has_form_fields(self, client):
        r = client.get('/runs/new/')
        data = r.data.decode()
        assert 'site_type' in data or 'LOG RUN' in data

    def test_run_detail_page_uses_db(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = SAMPLE_RUN
        mock_cur.fetchall.return_value = SAMPLE_LOOT
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/runs/1/')
        assert r.status_code == 200
        data = r.data.decode()
        assert 'Vale of Silent' in data or 'RUN #1' in data

    def test_run_detail_not_found(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/runs/99/')
        assert r.status_code == 404


class TestRunsAPI:

    def test_api_runs_returns_list(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [SAMPLE_RUN]
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/api/runs')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert isinstance(d, list)
        assert len(d) == 1

    def test_api_runs_empty(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/api/runs')
        assert r.status_code == 200
        assert json.loads(r.data) == []

    def test_api_runs_filter_by_type(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [SAMPLE_RUN]
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/api/runs?site_type=relic')
        assert r.status_code == 200

    def test_api_runs_filter_by_region(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [SAMPLE_RUN]
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/api/runs?region=Vale')
        assert r.status_code == 200

    def test_api_runs_filter_by_date(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/api/runs?date_from=2026-01-01&date_to=2026-03-31')
        assert r.status_code == 200

    def test_api_run_detail_returns_run(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = SAMPLE_RUN
        mock_cur.fetchall.return_value = SAMPLE_LOOT
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/api/runs/1')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['id'] == 1
        assert 'loot' in d

    def test_api_run_detail_not_found(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/api/runs/99')
        assert r.status_code == 404

    def test_api_new_run_success(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = {'id': 7}
        with patch('runs.get_db', return_value=mock_conn):
            r = client.post('/api/runs/new',
                json={'site_type': 'relic', 'region_name': 'Vale of Silent',
                      'security_class': 'WH', 'difficulty': 'superior',
                      'run_date': '2026-03-27', 'loot': []})
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['ok'] is True
        assert d['run_id'] == 7

    def test_api_new_run_with_loot(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = {'id': 8}
        loot = [
            {'item_name': 'Intact Armor Nanobot', 'item_category': 'artifacts',
             'quantity': 5, 'unit_price': 15000000.0},
        ]
        with patch('runs.get_db', return_value=mock_conn):
            r = client.post('/api/runs/new',
                json={'site_type': 'relic', 'region_name': 'Deklein', 'loot': loot})
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['ok'] is True

    def test_api_new_run_missing_region(self, client):
        r = client.post('/api/runs/new', json={'site_type': 'relic'})
        assert r.status_code == 400
        d = json.loads(r.data)
        assert 'error' in d

    def test_api_new_run_missing_type(self, client):
        r = client.post('/api/runs/new', json={'region_name': 'Vale'})
        assert r.status_code == 400

    def test_api_new_run_no_data(self, client):
        r = client.post('/api/runs/new', content_type='application/json', data='')
        assert r.status_code == 400

    def test_api_delete_run_success(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.rowcount = 1
        with patch('runs.get_db', return_value=mock_conn):
            r = client.delete('/api/runs/1')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['ok'] is True

    def test_api_delete_run_not_found(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.rowcount = 0
        with patch('runs.get_db', return_value=mock_conn):
            r = client.delete('/api/runs/99')
        assert r.status_code == 404

    def test_api_add_loot_success(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.side_effect = [{'id': 1}, {'id': 10}]
        with patch('runs.get_db', return_value=mock_conn):
            r = client.post('/api/runs/1/loot',
                json={'item_name': 'Intact Armor Nanobot', 'item_category': 'artifacts',
                      'quantity': 3, 'unit_price': 15000000.0})
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['ok'] is True

    def test_api_add_loot_missing_name(self, client):
        r = client.post('/api/runs/1/loot', json={'quantity': 1, 'unit_price': 1000})
        assert r.status_code == 400

    def test_api_add_loot_run_not_found(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None
        with patch('runs.get_db', return_value=mock_conn):
            r = client.post('/api/runs/99/loot',
                json={'item_name': 'Test Item', 'quantity': 1, 'unit_price': 0})
        assert r.status_code == 404

    def test_api_delete_loot_success(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = {'run_id': 1}
        with patch('runs.get_db', return_value=mock_conn):
            r = client.delete('/api/loot/1')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['ok'] is True

    def test_api_delete_loot_not_found(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None
        with patch('runs.get_db', return_value=mock_conn):
            r = client.delete('/api/loot/99')
        assert r.status_code == 404

    def test_api_regions_list(self, client):
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            {'region_name': 'Deklein'},
            {'region_name': 'Vale of Silent'},
        ]
        with patch('runs.get_db', return_value=mock_conn):
            r = client.get('/api/runs/regions/list')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert isinstance(d, list)
        assert 'Deklein' in d


class TestRunCalculations:

    def test_new_run_total_value_calculated(self, client):
        """Verify total_loot_value is sum of loot items."""
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = {'id': 5}

        loot = [
            {'item_name': 'Item A', 'item_category': 'artifacts', 'quantity': 2, 'unit_price': 10000000.0},
            {'item_name': 'Item B', 'item_category': 'salvage',   'quantity': 5, 'unit_price': 2000000.0},
        ]
        # Expected total: 2*10M + 5*2M = 30M

        captured_calls = []
        def capture_execute(q, p=None):
            captured_calls.append((q, p))
        mock_cur.execute.side_effect = capture_execute
        mock_cur.fetchone.return_value = {'id': 5}

        with patch('runs.get_db', return_value=mock_conn):
            r = client.post('/api/runs/new',
                json={'site_type': 'data', 'region_name': 'Pure Blind', 'loot': loot})
        assert r.status_code == 200

        # Find INSERT call for eeih_runs
        insert_calls = [c for c in captured_calls if 'INSERT INTO eeih_runs' in (c[0] or '')]
        assert insert_calls, 'No INSERT INTO eeih_runs found'
        # total_loot_value param should be 30M
        params = insert_calls[0][1]
        total_idx = 8  # 9th param (0-indexed)
        if params and len(params) > total_idx:
            assert params[total_idx] == 30000000.0

    def test_loot_items_inserted_per_item(self, client):
        """Verify each loot item is inserted individually."""
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = {'id': 6}

        loot = [
            {'item_name': 'A', 'item_category': 'artifacts', 'quantity': 1, 'unit_price': 5000000.0},
            {'item_name': 'B', 'item_category': 'datacores',  'quantity': 1, 'unit_price': 3000000.0},
            {'item_name': 'C', 'item_category': 'salvage',    'quantity': 1, 'unit_price': 1000000.0},
        ]
        calls = []
        mock_cur.execute.side_effect = lambda q, p=None: calls.append(q)

        with patch('runs.get_db', return_value=mock_conn):
            r = client.post('/api/runs/new', json={
                'site_type': 'relic', 'region_name': 'Test', 'loot': loot})
        assert r.status_code == 200
        loot_inserts = [c for c in calls if 'eeih_loot' in c and 'INSERT' in c]
        assert len(loot_inserts) == 3
