"""Loot blueprint — loot analysis, item breakdown, category stats."""
from flask import Blueprint, render_template, jsonify, request
from db import get_db, serialize_row

bp = Blueprint('loot', __name__)


@bp.route('/loot/')
def index():
    return render_template('partials/loot.html')


@bp.route('/api/loot/stats')
def api_stats():
    conn = get_db()
    try:
        cur = conn.cursor()

        # Aggregate totals
        cur.execute("""
            SELECT
                COUNT(*)                                       AS total_rows,
                SUM(quantity)                                  AS total_quantity,
                COALESCE(SUM(quantity * unit_price), 0)        AS total_value,
                COUNT(DISTINCT item_name)                      AS unique_items,
                COUNT(DISTINCT run_id)                         AS runs_with_loot
            FROM eeih_loot
        """)
        totals = serialize_row(cur.fetchone() or {})

        # Top 50 items by total value
        cur.execute("""
            SELECT
                item_name,
                item_category,
                SUM(quantity)                                  AS total_quantity,
                COALESCE(SUM(quantity * unit_price), 0)        AS total_value,
                COALESCE(AVG(unit_price), 0)                   AS avg_price,
                COUNT(DISTINCT run_id)                         AS found_in_runs
            FROM eeih_loot
            GROUP BY item_name, item_category
            ORDER BY total_value DESC
            LIMIT 50
        """)
        top_items = [serialize_row(r) for r in cur.fetchall()]

        # By category
        cur.execute("""
            SELECT
                item_category,
                COUNT(DISTINCT item_name)                      AS unique_items,
                SUM(quantity)                                  AS total_quantity,
                COALESCE(SUM(quantity * unit_price), 0)        AS total_value,
                COUNT(DISTINCT run_id)                         AS run_count
            FROM eeih_loot
            GROUP BY item_category
            ORDER BY total_value DESC
        """)
        by_category = [serialize_row(r) for r in cur.fetchall()]

        # Monthly loot value trend (last 6 months)
        cur.execute("""
            SELECT
                DATE_TRUNC('month', r.run_date)::DATE          AS month,
                COALESCE(SUM(l.quantity * l.unit_price), 0)    AS loot_value,
                COUNT(DISTINCT r.id)                           AS runs
            FROM eeih_runs r
            JOIN eeih_loot l ON l.run_id = r.id
            WHERE r.run_date >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY DATE_TRUNC('month', r.run_date)
            ORDER BY month
        """)
        monthly = [serialize_row(r) for r in cur.fetchall()]

        # Relic vs data loot value
        cur.execute("""
            SELECT
                r.site_type,
                COALESCE(SUM(l.quantity * l.unit_price), 0) AS total_loot_value,
                COUNT(DISTINCT r.id)                        AS run_count
            FROM eeih_runs r
            JOIN eeih_loot l ON l.run_id = r.id
            GROUP BY r.site_type
        """)
        by_type = [serialize_row(r) for r in cur.fetchall()]

        return jsonify({
            'totals':      totals,
            'top_items':   top_items,
            'by_category': by_category,
            'monthly':     monthly,
            'by_type':     by_type,
        })
    finally:
        conn.close()


@bp.route('/api/loot/items')
def api_items():
    category = request.args.get('category') or None
    conn = get_db()
    try:
        cur = conn.cursor()
        where  = ['1=1']
        params = []
        if category:
            where.append('l.item_category = %s')
            params.append(category)
        cur.execute(f"""
            SELECT l.id, l.run_id, l.item_name, l.item_category,
                   l.quantity, l.unit_price,
                   l.quantity * l.unit_price AS total_price,
                   r.region_name, r.run_date, r.site_type
            FROM eeih_loot l
            JOIN eeih_runs r ON r.id = l.run_id
            WHERE {' AND '.join(where)}
            ORDER BY total_price DESC
            LIMIT 500
        """, params if params else None)
        return jsonify([serialize_row(r) for r in cur.fetchall()])
    finally:
        conn.close()
