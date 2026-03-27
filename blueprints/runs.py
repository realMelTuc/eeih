"""Runs blueprint — log, list, detail, and delete exploration site runs."""
from flask import Blueprint, render_template, jsonify, request
from db import get_db, serialize_row

bp = Blueprint('runs', __name__)


@bp.route('/runs/')
def index():
    return render_template('partials/runs.html')


@bp.route('/runs/new/')
def new_run():
    return render_template('partials/run_new.html')


@bp.route('/runs/<int:run_id>/')
def run_detail(run_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM eeih_runs WHERE id = %s', [run_id])
        row = cur.fetchone()
        if not row:
            return '<div style="padding:40px;color:#ef4444;font-family:Geist Mono,monospace">Run #' + str(run_id) + ' not found.</div>', 404
        run = serialize_row(row)

        cur.execute("""
            SELECT id, item_name, item_category, quantity, unit_price,
                   quantity * unit_price AS total_price
            FROM eeih_loot
            WHERE run_id = %s
            ORDER BY (quantity * unit_price) DESC, item_name
        """, [run_id])
        loot = [serialize_row(r) for r in cur.fetchall()]

        return render_template('partials/run_detail.html', run=run, loot=loot)
    finally:
        conn.close()


# ── API endpoints ─────────────────────────────────────────────────────────────────

@bp.route('/api/runs')
def api_runs():
    site_type = request.args.get('site_type') or None
    region    = request.args.get('region') or None
    date_from = request.args.get('date_from') or None
    date_to   = request.args.get('date_to') or None

    conn = get_db()
    try:
        cur = conn.cursor()
        where  = ['1=1']
        params = []

        if site_type:
            where.append('r.site_type = %s')
            params.append(site_type)
        if region:
            where.append('r.region_name ILIKE %s')
            params.append(f'%{region}%')
        if date_from:
            where.append("r.run_date >= %s::DATE")
            params.append(date_from)
        if date_to:
            where.append("r.run_date <= %s::DATE")
            params.append(date_to)

        query = f"""
            SELECT r.id, r.site_type, r.site_name, r.region_name, r.system_name,
                   r.security_class, r.difficulty, r.run_date, r.total_loot_value,
                   r.run_time_seconds, r.notes, r.created_at,
                   COUNT(l.id) AS loot_count
            FROM eeih_runs r
            LEFT JOIN eeih_loot l ON l.run_id = r.id
            WHERE {' AND '.join(where)}
            GROUP BY r.id
            ORDER BY r.created_at DESC
            LIMIT 200
        """
        cur.execute(query, params if params else None)
        return jsonify([serialize_row(r) for r in cur.fetchall()])
    finally:
        conn.close()


@bp.route('/api/runs/<int:run_id>')
def api_run_detail(run_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, COUNT(l.id) AS loot_count
            FROM eeih_runs r
            LEFT JOIN eeih_loot l ON l.run_id = r.id
            WHERE r.id = %s
            GROUP BY r.id
        """, [run_id])
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404
        run = serialize_row(row)

        cur.execute("""
            SELECT id, item_name, item_category, quantity, unit_price,
                   quantity * unit_price AS total_price
            FROM eeih_loot
            WHERE run_id = %s
            ORDER BY (quantity * unit_price) DESC, item_name
        """, [run_id])
        run['loot'] = [serialize_row(r) for r in cur.fetchall()]
        return jsonify(run)
    finally:
        conn.close()


@bp.route('/api/runs/new', methods=['POST'])
def api_new_run():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    if not data.get('site_type'):
        return jsonify({'error': 'site_type required'}), 400
    if not data.get('region_name'):
        return jsonify({'error': 'region_name required'}), 400

    loot_items  = data.get('loot', [])
    total_value = sum(
        (int(item.get('quantity', 1) or 1)) * float(item.get('unit_price', 0) or 0)
        for item in loot_items
        if item.get('item_name')
    )

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO eeih_runs
                (site_type, site_name, region_name, system_name,
                 security_class, difficulty, run_date, run_time_seconds,
                 total_loot_value, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s::DATE, %s, %s, %s)
            RETURNING id
        """, [
            data['site_type'],
            data.get('site_name') or None,
            data['region_name'].strip(),
            data.get('system_name') or None,
            data.get('security_class', 'NS'),
            data.get('difficulty', 'standard'),
            data.get('run_date') or None,
            int(data['run_time_seconds']) if data.get('run_time_seconds') else None,
            total_value,
            data.get('notes') or None,
        ])
        run_id = cur.fetchone()['id']

        for item in loot_items:
            if not item.get('item_name'):
                continue
            cur.execute("""
                INSERT INTO eeih_loot (run_id, item_name, item_category, quantity, unit_price)
                VALUES (%s, %s, %s, %s, %s)
            """, [
                run_id,
                item['item_name'].strip(),
                item.get('item_category', 'misc'),
                max(1, int(item.get('quantity', 1) or 1)),
                float(item.get('unit_price', 0) or 0),
            ])

        conn.commit()
        return jsonify({'ok': True, 'run_id': run_id})
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@bp.route('/api/runs/<int:run_id>', methods=['DELETE'])
def api_delete_run(run_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM eeih_runs WHERE id = %s', [run_id])
        if cur.rowcount == 0:
            return jsonify({'error': 'Not found'}), 404
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


@bp.route('/api/runs/<int:run_id>/loot', methods=['POST'])
def api_add_loot(run_id):
    data = request.get_json()
    if not data or not data.get('item_name'):
        return jsonify({'error': 'item_name required'}), 400

    conn = get_db()
    try:
        cur = conn.cursor()

        # Verify run exists
        cur.execute('SELECT id FROM eeih_runs WHERE id = %s', [run_id])
        if not cur.fetchone():
            return jsonify({'error': 'Run not found'}), 404

        cur.execute("""
            INSERT INTO eeih_loot (run_id, item_name, item_category, quantity, unit_price)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, [
            run_id,
            data['item_name'].strip(),
            data.get('item_category', 'misc'),
            max(1, int(data.get('quantity', 1) or 1)),
            float(data.get('unit_price', 0) or 0),
        ])
        loot_id = cur.fetchone()['id']

        _recalc_run_total(cur, run_id)
        conn.commit()
        return jsonify({'ok': True, 'loot_id': loot_id})
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@bp.route('/api/loot/<int:loot_id>', methods=['DELETE'])
def api_delete_loot(loot_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('SELECT run_id FROM eeih_loot WHERE id = %s', [loot_id])
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404
        run_id = row['run_id']

        cur.execute('DELETE FROM eeih_loot WHERE id = %s', [loot_id])
        _recalc_run_total(cur, run_id)
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


@bp.route('/api/runs/regions/list')
def api_regions_list():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT region_name FROM eeih_runs ORDER BY region_name')
        return jsonify([r['region_name'] for r in cur.fetchall()])
    finally:
        conn.close()


def _recalc_run_total(cur, run_id):
    cur.execute("""
        UPDATE eeih_runs
        SET total_loot_value = (
            SELECT COALESCE(SUM(quantity * unit_price), 0)
            FROM eeih_loot WHERE run_id = %s
        )
        WHERE id = %s
    """, [run_id, run_id])
