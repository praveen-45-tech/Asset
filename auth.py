"""
routes/auth.py  ->  powers SCREEN 1 (AssetFlow login / create account)

Endpoints:
    POST /api/auth/signup   { name, email, password }
    POST /api/auth/login    { email, password }
    POST /api/auth/logout
    GET  /api/auth/me        -> who is currently logged in (used by every other screen
                                 to guard access and to fill the top-right user avatar)
"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, log_activity

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(force=True)
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not all([name, email, password]):
        return jsonify({"error": "name, email and password are required"}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "An account with this email already exists"}), 409

    # Matches the wireframe note: "Sign up creates an employee account, admin roles assigned later"
    conn.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'employee')",
        (name, email, generate_password_hash(password)),
    )
    conn.commit()
    user = conn.execute("SELECT id, name, email, role FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    session["user_id"] = user["id"]
    log_activity(f"New account created: {name}", "System")
    return jsonify(dict(user)), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email, password = data.get("email"), data.get("password")

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    conn = get_db()
    user = conn.execute("SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return jsonify(dict(user))
