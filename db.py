"""
db.py
-----
One shared place that knows how to talk to the database.
Every route file (routes/*.py) imports get_db() from here instead of
opening its own connection. This keeps all 10 screens reading/writing
the SAME database file: assetflow.db
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "assetflow.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_db():
    """Return a connection where rows behave like dictionaries (row['name'])."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """Wipes and rebuilds all tables from schema.sql. Run once via seed.py."""
    conn = get_db()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def log_activity(message, category="System"):
    """Every screen calls this so Screen 10 (Activity Logs) shows what happened.
    Kept for any route that calls it standalone (own connection, own commit) —
    just don't call this from inside a loop where another connection is
    already open with pending writes; insert directly on that connection instead."""
    conn = get_db()
    conn.execute(
        "INSERT INTO activity_logs (message, category) VALUES (?, ?)",
        (message, category),
    )
    conn.commit()
    conn.close()