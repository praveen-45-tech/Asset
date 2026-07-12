"""
routes/maintenance.py  ->  powers SCREEN 7 (Maintenance Management)

Kanban columns = the `status` field: Pending -> Approved -> In Progress -> Resolved
Wireframe note: "Approving a card moves the asset to Under maintenance,
resolving it returns it to Available." move_card() enforces exactly that.
"""
from flask import Blueprint, request, jsonify
from db import get_db, log_activity

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/api/maintenance")

VALID_STATUSES = ["Pending", "Approved", "In Progress", "Resolved"]


@maintenance_bp.route("", methods=["GET"])
def board():
    """Returns tickets grouped by column, ready for the kanban board."""
    conn = get_db()
    rows = conn.execute(
        "SELECT m.*, a.tag, a.name as asset_name FROM maintenance m "
        "JOIN assets a ON m.asset_id = a.id ORDER BY m.id"
    ).fetchall()
    conn.close()
    board = {s: [] for s in VALID_STATUSES}
    for r in rows:
        board[r["status"]].append(dict(r))
    return jsonify(board)


@maintenance_bp.route("", methods=["POST"])
def raise_ticket():
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute(
        "INSERT INTO maintenance (asset_id, issue, status) VALUES (?, ?, 'Pending')",
        (data["asset_id"], data["issue"]),
    )
    conn.commit()
    asset = conn.execute("SELECT tag FROM assets WHERE id=?", (data["asset_id"],)).fetchone()
    conn.close()
    log_activity(f"Maintenance requested for {asset['tag']}", "Approvals")
    return jsonify({"ok": True}), 201


@maintenance_bp.route("/<int:ticket_id>/move", methods=["PATCH"])
def move_card(ticket_id):
    """Drag a card to a new column. Also updates the linked asset's status."""
    data = request.get_json(force=True)
    new_status = data.get("status")
    if new_status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {VALID_STATUSES}"}), 400

    conn = get_db()
    ticket = conn.execute("SELECT * FROM maintenance WHERE id=?", (ticket_id,)).fetchone()
    if not ticket:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    conn.execute(
        "UPDATE maintenance SET status=?, technician=?, resolved_note=? WHERE id=?",
        (new_status, data.get("technician", ticket["technician"]),
         data.get("resolved_note", ticket["resolved_note"]), ticket_id),
    )

    if new_status == "Approved":
        conn.execute("UPDATE assets SET status='Maintenance' WHERE id=?", (ticket["asset_id"],))
    elif new_status == "Resolved":
        conn.execute("UPDATE assets SET status='Available' WHERE id=?", (ticket["asset_id"],))

    conn.commit()
    conn.close()
    log_activity(f"Maintenance ticket #{ticket_id} moved to {new_status}", "Approvals")
    return jsonify({"ok": True})
