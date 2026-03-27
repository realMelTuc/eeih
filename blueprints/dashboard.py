"""Dashboard blueprint — overview stats, recent runs, weekly trend."""
from flask import Blueprint, render_template, jsonify
from db import get_db, serialize_row

bp = Blueprint('dashboard', __name__)


@bp.route('/dashboard/')
def index():
    return render_template('partials/dashboard.html')


@bp.route('/api/dashboard/stats')
def api_stats():
    conn = get_db()
    try:
        cur = conn.cursor()

        # Overall aggregate stats
        cur.execute("""
            SELECT
                COUNT(*)                                                          AS total_runs,
                COALESCE(SUM(total_loot_value), 0)                               AS total_value,
                COALESCE(AVG(total_loot_value), 0)                               AS avg_value,
                COALESCE(MAX(total_loot_value), 0)                               AS best_run_value,
                COUNT(CASE WHEN site_type = 'relic' THEN 1 END)                  AS relic_runs,
                COUNT(CASE WHEN site_type = 'data'  THEN 1 END)                  AS data_runs,
                COUNT(CASE WHEN run_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END)   AS runs_this_week,
                COALESCE(SUM(CASE WHEN run_date >= CURRENT_DATE - INTERVAL '7 days'
                               THEN total_loot_value ELSE 0 END), 0)             AS value_this_week
            FROM eeih_runs
        """)
        stats = serialize_row(cur.fetchone() or {})

        # Top region by total value
        cur.execute("""
            SELECT region_name,
                   COALESCE(SUM(total_loot_value), 0) AS total_value,
                   COUNT(*)                            AS run_count
            FROM eeih_runs
            GROUP BY region_name
            ORDER BY total_value DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        stats['top_region'] = serialize_row(row) if row else None

        # Recent 15 runs
        cur.execute("""
            SELECT id, site_type, site_name, region_name, system_name,
                   security_class, difficulty, run_date, total_loot_value, run_time_seconds
            FROM eeih_runs
            ORDER BY created_at DESC
            LIMIT 15
        """)
        stats['recent_runs'] = [serialize_row(r) for r in cur.fetchall()]

        # Weekly trend — last 10 weeks
        cur.execute("""
            SELECT
                DATE_TRUNC('week', run_date)::DATE        AS week_start,
                COUNT(*)                                   AS runs,
                COALESCE(SUM(total_loot_value), 0)        AS total_value
            FROM eeih_runs
            WHERE run_date >= CURRENT_DATE - INTERVAL '70 days'
            GROUP BY DATE_TRUNC('week', run_date)
            ORDER BY week_start
        """)
        stats['weekly_trend'] = [serialize_row(r) for r in cur.fetchall()]

        # Security class breakdown
        cur.execute("""
            SELECT security_class,
                   COUNT(*) AS runs,
                   COALESCE(SUM(total_loot_value), 0) AS total_value
            FROM eeih_runs
            GROUP BY security_class
            ORDER BY total_value DESC
        """)
        stats['by_security'] = [serialize_row(r) for r in cur.fetchall()]

        return jsonify(stats)
    finally:
        conn.close()
