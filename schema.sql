-- AssetFlow database schema
-- Every screen maps to one or more of these tables (see README "Screen -> Table map")

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS allocations;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS maintenance;
DROP TABLE IF EXISTS audits;
DROP TABLE IF EXISTS audit_items;
DROP TABLE IF EXISTS activity_logs;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee',   -- 'admin' or 'employee'
    department_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    head TEXT,
    parent_dept TEXT,
    status TEXT NOT NULL DEFAULT 'Active'    -- Active / Inactive
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT UNIQUE NOT NULL,                -- e.g. AF-0019
    name TEXT NOT NULL,
    category TEXT,
    status TEXT NOT NULL DEFAULT 'Available',-- Available / Allocated / Maintenance / Damaged
    location TEXT,
    department_id INTEGER,
    allocated_to INTEGER,                    -- user id, nullable
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (allocated_to) REFERENCES users(id)
);

CREATE TABLE allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    from_user TEXT,
    to_user TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'Pending',  -- Pending / Approved / Rejected
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_name TEXT NOT NULL,
    booking_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    booked_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Confirmed',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    issue TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',  -- Pending / Approved / In Progress / Resolved
    technician TEXT,
    resolved_note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_name TEXT NOT NULL,               -- e.g. "Q3 audit: Engineering dept"
    department_id INTEGER,
    auditors TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT NOT NULL DEFAULT 'Open',    -- Open / Closed
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE audit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    expected_location TEXT,
    verification TEXT NOT NULL DEFAULT 'Pending', -- Verified / Missing / Damaged / Pending
    FOREIGN KEY (audit_id) REFERENCES audits(id),
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    category TEXT NOT NULL,                 -- Approvals / Bookings / Transfers / Audit / System
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
