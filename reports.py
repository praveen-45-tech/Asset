"""
routes/reports.py  ->  powers SCREEN 9 (Reports & Analytics)

Every number on this screen's charts (utilization by department,
maintenance frequency, most-used/idle assets) is computed live from the
same tables the other 9 screens write to - nothing here is hardcoded.
"""
from flask import Blueprint, jsonify
from db import get_db

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.route("/utilization", methods=["GET"])
def utilization_by_department():
    conn = get_db()
    rows = conn.execute(
        "SELECT d.name as department, "
        "SUM(CASE WHEN a.status='Allocated' THEN 1 ELSE 0 END) as allocated, "
        "COUNT(a.id) as total "
        "FROM departments d LEFT JOIN assets a ON a.department_id = d.id "
        "GROUP BY d.id"
    ).fetchall()
    conn.close()
    data = []
    for r in rows:
        pct = round((r["allocated"] / r["total"]) * 100) if r["total"] else 0
        data.append({"department": r["department"], "utilization_pct": pct, "total_assets": r["total"]})
    return jsonify(data)


@reports_bp.route("/maintenance-frequency", methods=["GET"])
def maintenance_frequency():
    conn = get_db()
    rows = conn.execute(
        "SELECT a.tag, a.name, COUNT(m.id) as ticket_count "
        "FROM assets a JOIN maintenance m ON m.asset_id = a.id "
        "GROUP BY a.id ORDER BY ticket_count DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@reports_bp.route("/most-used", methods=["GET"])
def most_used():
    conn = get_db()
    rows = conn.execute(
        "SELECT resource_name, COUNT(*) as bookings FROM bookings GROUP BY resource_name "
        "ORDER BY bookings DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@reports_bp.route("/idle", methods=["GET"])
def idle_assets():
    conn = get_db()
    rows = conn.execute(
        "SELECT tag, name, location, "
        "CAST(julianday('now') - julianday(created_at) AS INTEGER) as days_idle "
        "FROM assets WHERE status='Available' ORDER BY days_idle DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
