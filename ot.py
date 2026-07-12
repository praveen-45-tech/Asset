"""
OT (Overtime) Tracking blueprint.

Built against your actual schema: `allocations` (asset_id, from_user,
to_user, reason, status, due_at, returned_at) and `assets`
(status, allocated_to). `allocations.to_user` is a free-text name, not a
users.id — so ot_logs stores both `user_id` (resolved via assets.allocated_to,
may be NULL) and `holder_name` (always available) for display.

Uses your existing db.py helpers directly: get_db(), log_activity().
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

from db import get_db, log_activity

ot_bp = Blueprint("ot", __name__, url_prefix="/api/ot")


def _calc_overtime(due_at: str, grace_minutes: int, rate: float, cap: float):
    """Returns (ot_hours, ot_fine) as of right now, for a still-unreturned allocation."""
    fmt = "%Y-%m-%d %H:%M:%S"
    due = datetime.strptime(due_at, fmt)
    now = datetime.now()

    diff_minutes = (now - due).total_seconds() / 60
    if diff_minutes <= grace_minutes:
        return 0.0, 0.0

    ot_hours = round((diff_minutes - grace_minutes) / 60, 2)
    ot_fine = min(round(ot_hours * rate, 2), cap)
    return ot_hours, ot_fine


@ot_bp.route("/allocations/<int:allocation_id>/set-due", methods=["POST"])
def set_due_date(allocation_id):
    """
    Sets (or updates) the due date on an Approved allocation. Your existing
    approval flow (routes/allocation.py) has no due-date concept, so this
    is called separately after approval — e.g. a date picker on the OT screen,
    or right after approving in your existing allocation UI.
    Body: { "due_at": "2026-07-20 18:00:00" }  (or omit to default to +7 days)
    """
    payload = request.get_json(force=True) or {}
    due_at = payload.get("due_at")
    if not due_at:
        due_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    alloc = db.execute("SELECT * FROM allocations WHERE id = ?", (allocation_id,)).fetchone()
    if not alloc:
        db.close()
        return jsonify({"error": "allocation not found"}), 404

    db.execute("UPDATE allocations SET due_at = ? WHERE id = ?", (due_at, allocation_id))
    db.commit()
    db.close()
    log_activity(f"Due date set for allocation #{allocation_id}: {due_at}", "Transfers")
    return jsonify({"ok": True, "allocation_id": allocation_id, "due_at": due_at})


@ot_bp.route("/scan", methods=["POST"])
def scan_overdue():
    """
    Sweeps Approved allocations with a due_at in the past and no returned_at,
    and upserts ot_logs. Call from a 'Run OT Scan' button for the demo.
    """
    db = get_db()
    settings = db.execute("SELECT * FROM ot_settings WHERE id = 1").fetchone()

    overdue = db.execute("""
        SELECT al.id AS allocation_id, al.asset_id, al.to_user, al.due_at,
               a.allocated_to AS user_id
        FROM allocations al
        JOIN assets a ON a.id = al.asset_id
        WHERE al.status = 'Approved'
          AND al.returned_at IS NULL
          AND al.due_at IS NOT NULL
          AND al.due_at < datetime('now')
    """).fetchall()

    flagged = []
    for row in overdue:
        ot_hours, ot_fine = _calc_overtime(
            row["due_at"], settings["grace_minutes"],
            settings["fine_rate_per_hour"], settings["max_fine_cap"]
        )
        if ot_hours <= 0:
            continue

        existing = db.execute(
            "SELECT id FROM ot_logs WHERE allocation_id = ? AND status = 'ACTIVE'",
            (row["allocation_id"],)
        ).fetchone()

        if existing:
            db.execute("UPDATE ot_logs SET ot_hours = ?, ot_fine = ? WHERE id = ?",
                       (ot_hours, ot_fine, existing["id"]))
        else:
            db.execute("""
                INSERT INTO ot_logs (allocation_id, asset_id, user_id, holder_name, due_at, ot_hours, ot_fine, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
            """, (row["allocation_id"], row["asset_id"], row["user_id"], row["to_user"],
                  row["due_at"], ot_hours, ot_fine))
            log_activity(f"Overtime flagged: allocation #{row['allocation_id']} ({row['to_user']})", "Approvals")

        flagged.append({"allocation_id": row["allocation_id"], "ot_hours": ot_hours, "ot_fine": ot_fine})

    db.commit()
    db.close()
    return jsonify({"scanned": len(overdue), "flagged": flagged})


@ot_bp.route("/active", methods=["GET"])
def list_active_ot():
    db = get_db()
    rows = db.execute("""
        SELECT ot.*, a.name AS asset_name, a.tag AS asset_tag
        FROM ot_logs ot
        JOIN assets a ON a.id = ot.asset_id
        WHERE ot.status = 'ACTIVE'
        ORDER BY ot.ot_hours DESC
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@ot_bp.route("/<int:ot_id>/clear", methods=["POST"])
def clear_ot(ot_id):
    """Marks OT cleared and the allocation returned — frees the asset back up."""
    db = get_db()
    log = db.execute("SELECT * FROM ot_logs WHERE id = ?", (ot_id,)).fetchone()
    if not log:
        db.close()
        return jsonify({"error": "not found"}), 404

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute("UPDATE ot_logs SET status = 'CLEARED' WHERE id = ?", (ot_id,))
    db.execute("UPDATE allocations SET returned_at = ? WHERE id = ?", (now, log["allocation_id"]))
    db.execute("UPDATE assets SET status = 'Available', allocated_to = NULL WHERE id = ?", (log["asset_id"],))
    db.commit()
    db.close()
    log_activity(f"Asset returned, OT cleared (allocation #{log['allocation_id']})", "Transfers")
    return jsonify({"ok": True})


@ot_bp.route("/<int:ot_id>/waive", methods=["POST"])
def waive_ot(ot_id):
    """Waives the fine (manager override) without marking the asset returned."""
    db = get_db()
    db.execute("UPDATE ot_logs SET status = 'WAIVED', ot_fine = 0 WHERE id = ?", (ot_id,))
    db.commit()
    db.close()
    log_activity(f"OT fine waived (log #{ot_id})", "Approvals")
    return jsonify({"ok": True})


@ot_bp.route("/summary", methods=["GET"])
def summary():
    db = get_db()
    row = db.execute("""
        SELECT COUNT(*) AS active_count,
               COALESCE(SUM(ot_hours), 0) AS total_hours,
               COALESCE(SUM(ot_fine), 0) AS total_fines
        FROM ot_logs WHERE status = 'ACTIVE'
    """).fetchone()
    db.close()
    return jsonify(dict(row))
