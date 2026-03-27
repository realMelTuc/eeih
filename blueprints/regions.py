"""Regions blueprint — per-region performance comparison."""
from flask import Blueprint, render_template, jsonify
from db import get_db, serialize_row

bp = Blueprint('regions', __name__)


@bp.route('/regions/')
def index():
    return render_template('partials/regions.html')


@bp.route('/api/regions/stats')
def api_stats():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                region_name,
                COUNT(*)                                                              AS total_runs,
                COALESCE(SUM(total_loot_value), 0)                                   AS total_value,
                COALESCE(AVG(total_loot_value), 0)                                   AS avg_value,
                COALESCE(MAX(total_loot_value), 0)                                   AS best_run,
                COALESCE(MIN(CASE WHEN total_loot_value > 0 THEN total_loot_value END), 0) AS worst_run,
                MAX(run_date)                                                         AS last_run,
                COUNT(CASE WHEN site_type = 'relic' THEN 1 END)                      AS relic_count,
                COUNT(CASE WHEN site_type = 'data'  THEN 1 END)                      AS data_count,
                COUNT(CASE WHEN run_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) AS runs_30d,
                COALESCE(SUM(CASE WHEN run_date >= CURRENT_DATE - INTERVAL '30 days'
                                  THEN total_loot_value ELSE 0 END), 0)             AS value_30d
            FROM eeih_runs
            GROUP BY region_name
            ORDER BY total_value DESC
        """)
        regions = [serialize_row(r) for r in cur.fetchall()]
        return jsonify(regions)
    finally:
        conn.close()


@bp.route('/api/regions/<string:region_name>/runs')
def api_region_runs(region_name):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, site_type, site_name, system_name, security_class, difficulty,
                   run_date, total_loot_value, run_time_seconds
            FROM eeih_runs
            WHERE region_name = %s
            ORDER BY run_date DESC
            LIMIT 50
        """, [region_name])
        return jsonify([serialize_row(r) for r in cur.fetchall()])
    finally:
        conn.close()
