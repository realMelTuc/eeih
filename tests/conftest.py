"""Shared pytest fixtures for EEIH tests."""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Set up env before any imports
os.environ.setdefault('SUPABASE_DB_HOST', 'localhost')
os.environ.setdefault('SUPABASE_DB_NAME', 'test')
os.environ.setdefault('SUPABASE_DB_USER', 'test')
os.environ.setdefault('SUPABASE_DB_PASSWORD', 'test')
os.environ.setdefault('SUPABASE_DB_PORT', '5432')
os.environ.setdefault('SECRET_KEY', 'eeih-test-secret')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_mock_db(rows=None, one_row=None):
    """Create a mock DB connection/cursor pair."""
    mock_conn = MagicMock()
    mock_cur  = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    if one_row is not None:
        mock_cur.fetchone.return_value = one_row
    if rows is not None:
        mock_cur.fetchall.return_value = rows
    return mock_conn, mock_cur


@pytest.fixture
def mock_db_empty():
    conn, cur = make_mock_db(rows=[], one_row=None)
    return conn, cur


@pytest.fixture
def mock_db_run():
    run = {
        'id': 1, 'site_type': 'relic', 'site_name': 'Superior Sleeper Cache',
        'region_name': 'Vale of Silent', 'system_name': 'J123456',
        'security_class': 'WH', 'difficulty': 'superior',
        'run_date': '2026-03-27', 'total_loot_value': 142000000.0,
        'run_time_seconds': 900, 'notes': None, 'created_at': '2026-03-27T10:00:00',
        'loot_count': 3
    }
    conn, cur = make_mock_db(rows=[run], one_row=run)
    return conn, cur


@pytest.fixture
def mock_db_loot():
    items = [
        {'id': 1, 'run_id': 1, 'item_name': 'Intact Armor Nanobot',
         'item_category': 'artifacts', 'quantity': 5, 'unit_price': 15000000.0,
         'total_price': 75000000.0},
        {'id': 2, 'run_id': 1, 'item_name': 'Malfunctioning Hull Section',
         'item_category': 'artifacts', 'quantity': 3, 'unit_price': 22000000.0,
         'total_price': 66000000.0},
    ]
    conn, cur = make_mock_db(rows=items, one_row=items[0])
    return conn, cur


@pytest.fixture
def mock_db_regions():
    regions = [
        {'region_name': 'Vale of Silent', 'total_runs': 5, 'total_value': 520000000.0,
         'avg_value': 104000000.0, 'best_run': 210000000.0, 'worst_run': 31000000.0,
         'last_run': '2026-03-27', 'relic_count': 4, 'data_count': 1,
         'runs_30d': 3, 'value_30d': 280000000.0},
        {'region_name': 'Deklein', 'total_runs': 3, 'total_value': 240000000.0,
         'avg_value': 80000000.0, 'best_run': 110000000.0, 'worst_run': 45000000.0,
         'last_run': '2026-03-25', 'relic_count': 2, 'data_count': 1,
         'runs_30d': 2, 'value_30d': 190000000.0},
    ]
    conn, cur = make_mock_db(rows=regions)
    return conn, cur


@pytest.fixture
def app():
    with patch('db.get_db'):
        import importlib
        import app as application
        importlib.reload(application)
        application.app.config['TESTING'] = True
        application.app.config['SECRET_KEY'] = 'test'
        return application.app


@pytest.fixture
def client(app):
    return app.test_client()
