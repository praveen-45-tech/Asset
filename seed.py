"""
seed.py
-------
Run this ONCE (and any time you want a fresh demo dataset):
    python seed.py

It rebuilds assetflow.db and fills it with sample departments, users,
assets, bookings, maintenance tickets etc, so all 10 screens have
believable data the moment you open them - important for a hackathon demo.
"""
from db import init_db, get_db, log_activity
from werkzeug.security import generate_password_hash

print("Building database from schema.sql ...")
init_db()
conn = get_db()
cur = conn.cursor()

# ---- Departments (Screen 3) ----
departments = [
    ("Engineering", "Aditi Rao", None, "Active"),
    ("Facilities", "Rohan Mehta", None, "Active"),
    ("Field Ops", "Sana Iqbal", "Engineering", "Inactive"),
]
cur.executemany(
    "INSERT INTO departments (name, head, parent_dept, status) VALUES (?,?,?,?)",
    departments,
)

# ---- Categories (Screen 3) ----
categories = ["Electronics", "Furniture", "Vehicles", "Tools"]
cur.executemany("INSERT INTO categories (name) VALUES (?)", [(c,) for c in categories])

# ---- Users (Screen 1 signup / Screen 3 employees) ----
users = [
    ("Admin User", "admin@company.com", generate_password_hash("admin123"), "admin", 1),
    ("Priya Shah", "priya@company.com", generate_password_hash("password123"), "employee", 1),
    ("Arjun Nair", "arjun@company.com", generate_password_hash("password123"), "employee", 2),
]
cur.executemany(
    "INSERT INTO users (name, email, password_hash, role, department_id) VALUES (?,?,?,?,?)",
    users,
)

# ---- Assets (Screen 4) ----
assets = [
    ("AF-0019", "Dell Laptop", "Electronics", "Allocated", "Bengaluru", 1, 2),
    ("AF-0062", "Projector", "Electronics", "Maintenance", "HQ Floor 2", 1, None),
    ("AF-0201", "Office Chair", "Furniture", "Available", "Warehouse", 2, None),
    ("AF-0003", "Dell Laptop", "Electronics", "Available", "Desk E12", 1, None),
    ("AF-0421", "Office Chair", "Furniture", "Available", "Desk E14", 1, None),
    ("AF-0838", "Monitor", "Electronics", "Available", "Desk E16", 1, None),
]
cur.executemany(
    "INSERT INTO assets (tag, name, category, status, location, department_id, allocated_to) VALUES (?,?,?,?,?,?,?)",
    assets,
)

# ---- Allocation history (Screen 5) ----
cur.execute(
    "INSERT INTO allocations (asset_id, from_user, to_user, reason, status) VALUES (1, NULL, 'Priya Shah', 'Onboarding', 'Approved')"
)

# ---- Bookings (Screen 6) ----
cur.execute(
    "INSERT INTO bookings (resource_name, booking_date, start_time, end_time, booked_by, status) "
    "VALUES ('Conference Room B2', '2026-07-14', '09:00', '10:00', 'Procurement Team', 'Confirmed')"
)

# ---- Maintenance (Screen 7) ----
maintenance = [
    (2, "Projector bulb not turning on", "Pending", None, None),
    (4, "AC unit noisy compressor", "Approved", "Tech R", None),
]
cur.executemany(
    "INSERT INTO maintenance (asset_id, issue, status, technician, resolved_note) VALUES (?,?,?,?,?)",
    maintenance,
)

# ---- Audit cycle (Screen 8) ----
cur.execute(
    "INSERT INTO audits (cycle_name, department_id, auditors, start_date, end_date, status) "
    "VALUES ('Q3 audit: Engineering dept', 1, 'A. Rao, S. Iqbal', '2026-07-01', '2026-07-15', 'Open')"
)
cur.execute(
    "INSERT INTO audit_items (audit_id, asset_id, expected_location, verification) VALUES (1, 4, 'Desk E12', 'Verified')"
)
cur.execute(
    "INSERT INTO audit_items (audit_id, asset_id, expected_location, verification) VALUES (1, 5, 'Desk E14', 'Missing')"
)
cur.execute(
    "INSERT INTO audit_items (audit_id, asset_id, expected_location, verification) VALUES (1, 6, 'Desk E16', 'Damaged')"
)

conn.commit()
conn.close()

log_activity("Demo data seeded", "System")
print("Done. Log in with admin@company.com / admin123")
