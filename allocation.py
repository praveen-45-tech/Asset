"""
routes/allocation.py  ->  powers SCREEN 5 (Asset allocation & Transfer)

Core business rule shown in the wireframe:
  "Already allocated to Priya Shah (Engineering) - Direct re-allocation is
   blocked - submit a transfer request below"

So: if an asset is already Allocated, a direct re-allocation is rejected
(409) and the caller must go through /transfer-request instead, which
creates a Pending allocation row for an admin to approve.
"""
from flask import Blueprint, request, jsonify
from db import get_db, log_activity

allocation_bp = Blueprint("allocation", __name__, url_prefix="/api/allocations")


@allocation_bp.route("/asset/<int:asset_id>", methods=["GET"])
def asset_allocation_state(asset_id):
    """Returns current status + full history for the allocation screen's right-hand panel."""
    conn = get_db()
    asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    if not asset:
        conn.close()
        return jsonify({"error": "Asset not found"}), 404

    history = conn.execute(
        "SELECT * FROM allocations WHERE asset_id=? ORDER BY id DESC", (asset_id,)
    ).fetchall()
    holder = None
    if asset["allocated_to"]:
        holder = conn.execute("SELECT name FROM users WHERE id=?", (asset["allocated_to"],)).fetchone()
    conn.close()

    return jsonify({
        "asset": dict(asset),
        "currently_allocated_to": holder["name"] if holder else None,
        "blocked": asset["status"] == "Allocated",
        "history": [dict(h) for h in history],
    })


@allocation_bp.route("", methods=["POST"])
def allocate_asset():
    """Direct allocation - only works if the asset is currently Available."""
    data = request.get_json(force=True)
    asset_id = data["asset_id"]
    conn = get_db()
    asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()

    if not asset:
        conn.close()
        return jsonify({"error": "Asset not found"}), 404

    if asset["status"] == "Allocated":
        conn.close()
        return jsonify({
            "error": "Already allocated - direct re-allocation is blocked. Submit a transfer request instead."
        }), 409

    conn.execute(
        "INSERT INTO allocations (asset_id, from_user, to_user, reason, status) VALUES (?,?,?,?, 'Approved')",
        (asset_id, data.get("from_user"), data.get("to_user"), data.get("reason")),
    )
    conn.execute("UPDATE assets SET status='Allocated' WHERE id=?", (asset_id,))
    conn.commit()
    conn.close()
    log_activity(f"Asset {asset['tag']} allocated to {data.get('to_user')}", "Transfers")
    return jsonify({"ok": True}), 201


@allocation_bp.route("/transfer-request", methods=["POST"])
def transfer_request():
    """Used when the asset is already allocated - creates a Pending row for admin approval."""
    data = request.get_json(force=True)
    asset_id = data["asset_id"]
    conn = get_db()
    conn.execute(
        "INSERT INTO allocations (asset_id, from_user, to_user, reason, status) VALUES (?,?,?,?, 'Pending')",
        (asset_id, data.get("from_user"), data.get("to_user"), data.get("reason")),
    )
    conn.commit()
    asset = conn.execute("SELECT tag FROM assets WHERE id=?", (asset_id,)).fetchone()
    conn.close()
    log_activity(f"Transfer requested for {asset['tag']} to {data.get('to_user')}", "Transfers")
    return jsonify({"ok": True}), 201


@allocation_bp.route("/<int:allocation_id>/approve", methods=["PATCH"])
def approve_transfer(allocation_id):
    """Admin approves a pending transfer - moves the asset to the new holder."""
    conn = get_db()
    alloc = conn.execute("SELECT * FROM allocations WHERE id=?", (allocation_id,)).fetchone()
    if not alloc:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    conn.execute("UPDATE allocations SET status='Approved' WHERE id=?", (allocation_id,))
    conn.execute("UPDATE assets SET status='Allocated' WHERE id=?", (alloc["asset_id"],))
    conn.commit()
    conn.close()
    log_activity(f"Transfer #{allocation_id} approved", "Transfers")
    return jsonify({"ok": True})
