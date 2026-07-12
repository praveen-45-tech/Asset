"""
routes/audit.py  ->  powers SCREEN 8 (Asset Audit)

Wireframe note: "2 assets flagged - discrepancy report generated
automatically". discrepancy_count() computes that from audit_items
instead of a human tallying it, and close_cycle() locks the audit.
"""
from flask import Blueprint, request, jsonify
from db import get_db, log_activity

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audits")


@audit_bp.route("", methods=["GET"])
def list_audits():
    conn = get_db()
    rows = conn.execute(
        "SELECT au.*, d.name as department_name FROM audits au "
        "LEFT JOIN departments d ON au.department_id = d.id ORDER BY au.id DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@audit_bp.route("", methods=["POST"])
def start_audit():
    data = request.get_json(force=True)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO audits (cycle_name, department_id, auditors, start_date, end_date, status) "
        "VALUES (?,?,?,?,?, 'Open')",
        (data["cycle_name"], data.get("department_id"), data.get("auditors"),
         data.get("start_date"), data.get("end_date")),
    )
    audit_id = cur.lastrowid

    # Snapshot every asset in the department as a checklist row to verify
    if data.get("department_id"):
        assets = conn.execute(
            "SELECT id, location FROM assets WHERE department_id=?", (data["department_id"],)
        ).fetchall()
        for a in assets:
            conn.execute(
                "INSERT INTO audit_items (audit_id, asset_id, expected_location, verification) "
                "VALUES (?, ?, ?, 'Pending')",
                (audit_id, a["id"], a["location"]),
            )
    conn.commit()
    conn.close()
    log_activity(f"Audit cycle started: {data['cycle_name']}", "Audit")
    return jsonify({"ok": True, "audit_id": audit_id}), 201


@audit_bp.route("/<int:audit_id>/items", methods=["GET"])
def audit_items(audit_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT ai.*, a.tag, a.name FROM audit_items ai "
        "JOIN assets a ON ai.asset_id = a.id WHERE ai.audit_id=?", (audit_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@audit_bp.route("/items/<int:item_id>", methods=["PATCH"])
def verify_item(item_id):
    data = request.get_json(force=True)
    verification = data.get("verification")  # Verified / Missing / Damaged
    conn = get_db()
    conn.execute("UPDATE audit_items SET verification=? WHERE id=?", (verification, item_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@audit_bp.route("/<int:audit_id>/discrepancies", methods=["GET"])
def discrepancy_count(audit_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT COUNT(*) c FROM audit_items WHERE audit_id=? AND verification IN ('Missing','Damaged')",
        (audit_id,),
    ).fetchone()
    conn.close()
    return jsonify({"flagged": rows["c"]})


@audit_bp.route("/<int:audit_id>/close", methods=["PATCH"])
def close_cycle(audit_id):
    conn = get_db()
    conn.execute("UPDATE audits SET status='Closed' WHERE id=?", (audit_id,))
    conn.commit()
    conn.close()
    log_activity(f"Audit cycle #{audit_id} closed", "Audit")
    return jsonify({"ok": True})
