"""
routes/org.py  ->  powers SCREEN 3 (Organization setup - Admin only)

Editing a department here is the single source of truth that drives the
department picklist used later in Screen 4 (asset registration) and
Screen 9 (reports by department) - exactly like the sticky note on the
wireframe says.
"""
from flask import Blueprint, request, jsonify
from db import get_db, log_activity

org_bp = Blueprint("org", __name__, url_prefix="/api/org")


@org_bp.route("/departments", methods=["GET"])
def list_departments():
    conn = get_db()
    rows = conn.execute("SELECT * FROM departments ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@org_bp.route("/departments", methods=["POST"])
def add_department():
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute(
        "INSERT INTO departments (name, head, parent_dept, status) VALUES (?,?,?,?)",
        (data.get("name"), data.get("head"), data.get("parent_dept"), data.get("status", "Active")),
    )
    conn.commit()
    conn.close()
    log_activity(f"Department created: {data.get('name')}", "System")
    return jsonify({"ok": True}), 201


@org_bp.route("/departments/<int:dept_id>", methods=["PATCH"])
def update_department(dept_id):
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute(
        "UPDATE departments SET name=?, head=?, parent_dept=?, status=? WHERE id=?",
        (data.get("name"), data.get("head"), data.get("parent_dept"), data.get("status"), dept_id),
    )
    conn.commit()
    conn.close()
    log_activity(f"Department #{dept_id} updated", "System")
    return jsonify({"ok": True})


@org_bp.route("/categories", methods=["GET"])
def list_categories():
    conn = get_db()
    rows = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@org_bp.route("/categories", methods=["POST"])
def add_category():
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute("INSERT INTO categories (name) VALUES (?)", (data.get("name"),))
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 201


@org_bp.route("/employees", methods=["GET"])
def list_employees():
    conn = get_db()
    rows = conn.execute(
        "SELECT u.id, u.name, u.email, u.role, d.name as department "
        "FROM users u LEFT JOIN departments d ON u.department_id = d.id ORDER BY u.id"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
