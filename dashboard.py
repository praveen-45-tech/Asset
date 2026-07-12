"""
routes/dashboard.py  ->  powers SCREEN 2 (Today's Overview)

One endpoint that rolls up numbers from assets, bookings, allocations
and maintenance so the dashboard cards match what's really in the DB
instead of being hardcoded.
"""
from flask import Blueprint, jsonify
from db import get_db

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/overview", methods=["GET"])
def overview():
    conn = get_db()

    available = conn.execute("SELECT COUNT(*) c FROM assets WHERE status='Available'").fetchone()["c"]
    allocated = conn.execute("SELECT COUNT(*) c FROM assets WHERE status='Allocated'").fetchone()["c"]
    maintenance = conn.execute("SELECT COUNT(*) c FROM assets WHERE status='Maintenance'").fetchone()["c"]

    active_bookings = conn.execute(
        "SELECT COUNT(*) c FROM bookings WHERE booking_date >= date('now')"
    ).fetchone()["c"]
    pending_transfers = conn.execute(
        "SELECT COUNT(*) c FROM allocations WHERE status='Pending'"
    ).fetchone()["c"]
    upcoming_returns = conn.execute(
        "SELECT COUNT(*) c FROM assets WHERE status='Allocated'"
    ).fetchone()["c"]

    overdue = conn.execute(
        "SELECT a.tag, a.name FROM assets a WHERE a.status='Allocated' "
        "AND a.id IN (SELECT asset_id FROM allocations WHERE status='Approved') LIMIT 3"
    ).fetchall()

    recent = conn.execute(
        "SELECT message, category, created_at FROM activity_logs ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()
    return jsonify({
        "available": available,
        "allocated": allocated,
        "maintenance_flagged": maintenance,
        "active_bookings": active_bookings,
        "pending_transfers": pending_transfers,
        "upcoming_returns": upcoming_returns,
        "overdue_assets": [dict(r) for r in overdue],
        "recent_activity": [dict(r) for r in recent],
    })
