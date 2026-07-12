"""
routes/assets.py  ->  powers SCREEN 4 (Asset registration and directory)

Search box on that screen searches by tag, name, or QR code - the GET
endpoint below accepts a ?q= for exactly that.
"""
from flask import Blueprint, request, jsonify
from db import get_db, log_activity

assets_bp = Blueprint("assets", __name__, url_prefix="/api/assets")


@assets_bp.route("", methods=["GET"])
def list_assets():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    status = request.args.get("status", "")
    department_id = request.args.get("department", "")

    conn = get_db()
    sql = (
        "SELECT a.*, d.name as department_name FROM assets a "
        "LEFT JOIN departments d ON a.department_id = d.id WHERE 1=1"
    )
    params = []
    if q:
        sql += " AND (a.tag LIKE ? OR a.name LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND a.category = ?"
        params.append(category)
    if status:
        sql += " AND a.status = ?"
        params.append(status)
    if department_id:
        sql += " AND a.department_id = ?"
        params.append(department_id)
    sql += " ORDER BY a.id DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@assets_bp.route("", methods=["POST"])
def register_asset():
    data = request.get_json(force=True)
    conn = get_db()

    # auto-generate the next tag, e.g. AF-0245, if not supplied
    tag = data.get("tag")
    if not tag:
        last = conn.execute("SELECT tag FROM assets ORDER BY id DESC LIMIT 1").fetchone()
        next_num = int(last["tag"].split("-")[1]) + 1 if last else 1
        tag = f"AF-{next_num:04d}"

    conn.execute(
        "INSERT INTO assets (tag, name, category, status, location, department_id) VALUES (?,?,?,?,?,?)",
        (tag, data.get("name"), data.get("category"), data.get("status", "Available"),
         data.get("location"), data.get("department_id")),
    )
    conn.commit()
    conn.close()
    log_activity(f"Asset registered: {tag} - {data.get('name')}", "System")
    return jsonify({"ok": True, "tag": tag}), 201


@assets_bp.route("/<int:asset_id>", methods=["GET"])
def get_asset(asset_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))
