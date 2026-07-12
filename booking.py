"""
routes/booking.py  ->  powers SCREEN 6 (Resource booking)

Wireframe shows a conflict: "Requested 9:30 to 10:30 - conflict - slot is
unavailable" because 9:00-10:00 is already booked. check_conflict() does
that overlap math before ever inserting a row.
"""
from flask import Blueprint, request, jsonify
from db import get_db, log_activity

booking_bp = Blueprint("booking", __name__, url_prefix="/api/bookings")


def overlaps(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a


@booking_bp.route("", methods=["GET"])
def list_bookings():
    resource = request.args.get("resource", "")
    date = request.args.get("date", "")
    conn = get_db()
    sql = "SELECT * FROM bookings WHERE 1=1"
    params = []
    if resource:
        sql += " AND resource_name = ?"
        params.append(resource)
    if date:
        sql += " AND booking_date = ?"
        params.append(date)
    sql += " ORDER BY start_time"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@booking_bp.route("/check", methods=["POST"])
def check_availability():
    """Called live as the user picks a time slot, before they hit 'Book a slot'."""
    data = request.get_json(force=True)
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM bookings WHERE resource_name=? AND booking_date=? AND status='Confirmed'",
        (data["resource_name"], data["booking_date"]),
    ).fetchall()
    conn.close()

    for b in existing:
        if overlaps(data["start_time"], data["end_time"], b["start_time"], b["end_time"]):
            return jsonify({
                "available": False,
                "conflict_with": f"{b['booked_by']} ({b['start_time']}-{b['end_time']})"
            })
    return jsonify({"available": True})


@booking_bp.route("", methods=["POST"])
def create_booking():
    data = request.get_json(force=True)
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM bookings WHERE resource_name=? AND booking_date=? AND status='Confirmed'",
        (data["resource_name"], data["booking_date"]),
    ).fetchall()

    for b in existing:
        if overlaps(data["start_time"], data["end_time"], b["start_time"], b["end_time"]):
            conn.close()
            return jsonify({"error": "Slot is unavailable - conflicts with an existing booking"}), 409

    conn.execute(
        "INSERT INTO bookings (resource_name, booking_date, start_time, end_time, booked_by, status) "
        "VALUES (?,?,?,?,?, 'Confirmed')",
        (data["resource_name"], data["booking_date"], data["start_time"], data["end_time"], data["booked_by"]),
    )
    conn.commit()
    conn.close()
    log_activity(f"{data['resource_name']} booked by {data['booked_by']}", "Bookings")
    return jsonify({"ok": True}), 201
