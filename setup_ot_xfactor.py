"""
setup_ot_xfactor.py
--------------------
ONE file. Does everything. No separate .sql file needed.

HOW TO USE:
1. Save this file directly into: D:\\assetflow\\assetflow\\backend
   (right-click backend folder in VS Code -> New File -> name it
   setup_ot_xfactor.py -> paste this whole thing in -> save)
2. In VS Code terminal, run:
       python setup_ot_xfactor.py
3. Read the output. It will say SUCCESS or tell you exactly what's wrong.
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "assetflow.db")

SCHEMA_SQL = """
ALTER TABLE allocations ADD COLUMN due_at TEXT;
ALTER TABLE allocations ADD COLUMN returned_at TEXT;

CREATE TABLE IF NOT EXISTS ot_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    allocation_id   INTEGER NOT NULL,
    asset_id        INTEGER NOT NULL,
    user_id         INTEGER,
    holder_name     TEXT,
    due_at          TEXT NOT NULL,
    ot_hours        REAL DEFAULT 0,
    ot_fine         REAL DEFAULT 0,
    status          TEXT DEFAULT 'ACTIVE',
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (allocation_id) REFERENCES allocations(id),
    FOREIGN KEY (asset_id)      REFERENCES assets(id),
    FOREIGN KEY (user_id)       REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS ot_settings (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),
    grace_minutes       INTEGER DEFAULT 15,
    fine_rate_per_hour  REAL DEFAULT 50.0,
    max_fine_cap        REAL DEFAULT 2000.0
);
INSERT OR IGNORE INTO ot_settings (id, grace_minutes, fine_rate_per_hour, max_fine_cap)
VALUES (1, 15, 50.0, 2000.0);

CREATE TABLE IF NOT EXISTS asset_risk_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        INTEGER NOT NULL,
    risk_score      REAL NOT NULL,
    risk_band       TEXT NOT NULL,
    factors_json    TEXT,
    ai_explanation  TEXT,
    computed_at     TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE IF NOT EXISTS ai_recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    request_context TEXT,
    recommendation  TEXT NOT NULL,
    reasoning       TEXT,
    confidence      REAL,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

EXPECTED_TABLES = {"ot_logs", "ot_settings", "asset_risk_scores", "ai_recommendations"}
EXPECTED_COLUMNS = {"due_at", "returned_at"}


def main():
    print("=" * 60)
    print(f"Database path: {DB_PATH}")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print("\n❌ PROBLEM: assetflow.db does not exist here.")
        print("Fix: run `python seed.py` first, then run this script again.")
        return

    conn = sqlite3.connect(DB_PATH)

    # Apply each statement one at a time, so if a column/table already
    # exists from a previous partial attempt, we just skip it and continue
    # instead of stopping.
    statements = [s.strip() for s in SCHEMA_SQL.split(";") if s.strip()]
    applied, skipped = 0, 0
    for stmt in statements:
        try:
            conn.execute(stmt)
            applied += 1
        except sqlite3.OperationalError as e:
            skipped += 1
            print(f"  (skipped, likely already exists: {e})")
    conn.commit()

    print(f"\nApplied {applied} statements, skipped {skipped} (already existed).")

    # Verify
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    columns = {r[1] for r in conn.execute("PRAGMA table_info(allocations)")}

    print("\n--- VERIFICATION ---")
    print("New tables present:")
    for t in sorted(EXPECTED_TABLES):
        mark = "✅" if t in tables else "❌ MISSING"
        print(f"  {mark}  {t}")

    print("New columns on 'allocations':")
    for c in sorted(EXPECTED_COLUMNS):
        mark = "✅" if c in columns else "❌ MISSING"
        print(f"  {mark}  {c}")

    missing_tables = EXPECTED_TABLES - tables
    missing_columns = EXPECTED_COLUMNS - columns

    print()
    if not missing_tables and not missing_columns:
        print("🎉 SUCCESS — everything is in place.")
        print("Now restart app.py (Ctrl+C in its terminal, then `python app.py` again),")
        print("then refresh the AI Insights / Overtime Control pages in your browser.")
    else:
        print("⚠ Still incomplete. Copy this ENTIRE output and send it back.")

    conn.close()


if __name__ == "__main__":
    main()
