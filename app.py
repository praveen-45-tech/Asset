"""
app.py
------
The single entry point. Run this file to start EVERYTHING:
    python app.py

What it does:
1. Creates the Flask app
2. Registers one "blueprint" per screen's API (routes/*.py)
3. Serves the frontend/ folder as static files, so you open
   http://127.0.0.1:5000/ and the WHOLE app (frontend + backend) just works -
   no separate frontend server, no CORS headaches.
"""
import os
from flask import Flask, send_from_directory, session, jsonify
from functools import wraps

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.org import org_bp
from routes.assets import assets_bp
from routes.allocation import allocation_bp
from routes.booking import booking_bp
from routes.maintenance import maintenance_bp
from routes.audit import audit_bp
from routes.reports import reports_bp
from routes.activity import activity_bp

# --- new for hackathon: OT tracking + X-Factor AI Insight Engine ---
from routes.ot import ot_bp
from routes.xfactor import xfactor_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = "change-this-secret-key-before-you-deploy"  # fine for a hackathon demo

# ---- Register every screen's API blueprint ----
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(org_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(allocation_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(maintenance_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(activity_bp)

# --- new for hackathon ---
app.register_blueprint(ot_bp)
app.register_blueprint(xfactor_bp)


# ---- Serve the frontend ----
@app.route("/")
def serve_login():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == "__main__":
    if not os.path.exists(os.path.join(BASE_DIR, "assetflow.db")):
        print("No database found - run `python seed.py` first!")
    app.run(debug=True, port=5000)
