"""
routes/activity.py  ->  powers SCREEN 10 (Activity logs & Notifications)

This is deliberately the simplest file: every other route file already
calls log_activity() from db.py whenever something meaningful happens
(asset registered, transfer approved, booking made, maintenance moved,
audit closed...). This endpoint just reads that shared table back,
optionally filtered by the tab the user clicked (Approvals / Bookings).
"""
from flask import Blueprint, request, jsonify
from db import get_db

activity_bp = Blueprint("activity", __name__, url_prefix="/api/activity")


@activity_bp.route("", methods=["GET"])
def list_activity():
    category = request.args.get("category", "")
    conn = get_db()
    if category and category != "All":
        rows = conn.execute(
            "SELECT * FROM activity_logs WHERE category=? ORDER BY id DESC LIMIT 100", (category,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
