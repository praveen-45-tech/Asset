"""
apply_schema.py
----------------
Run this once to add the OT + AI Insights tables to your database.

HOW TO USE:
1. Put this file in the SAME folder as assetflow.db and schema_additions.sql
   (that's your backend/ folder).
2. Open a terminal in that folder and run:
       python apply_schema.py
3. It will print which tables exist before and after, so you can confirm
   it worked.

No need to type any file paths — it just looks in its own folder.
"""
import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "assetflow.db")
SQL_PATH = os.path.join(BASE_DIR, "schema_additions.sql")

def list_tables(conn):
    return sorted(r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ))

def main():
    print(f"Looking for database at: {DB_PATH}")
    print(f"Looking for schema file at: {SQL_PATH}")
    print()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: assetflow.db not found in {BASE_DIR}")
        print("Make sure this script is in the same folder as assetflow.db (your backend/ folder),")
        print("and that you've already run `python seed.py` at least once.")
        sys.exit(1)

    if not os.path.exists(SQL_PATH):
        print(f"ERROR: schema_additions.sql not found in {BASE_DIR}")
        print("Move or copy schema_additions.sql into this same folder, then run this script again.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    print("Tables BEFORE:", list_tables(conn))

    with open(SQL_PATH, "r") as f:
        sql = f.read()

    try:
        conn.executescript(sql)
        conn.commit()
    except sqlite3.OperationalError as e:
        # Common case: columns/tables already exist from a previous partial run
        print(f"\nNote: {e}")
        print("This usually just means it was already partly applied. Continuing to check tables...")

    print("Tables AFTER: ", list_tables(conn))

    expected = {"ot_logs", "ot_settings", "asset_risk_scores", "ai_recommendations"}
    after = set(list_tables(conn))
    missing = expected - after

    print()
    if missing:
        print(f"⚠ Still missing: {missing}")
        print("Something went wrong — copy the full output above and send it back for help.")
    else:
        print("✅ All 4 new tables are present. You're good to go — restart app.py if it's running.")

    conn.close()

if __name__ == "__main__":
    main()
