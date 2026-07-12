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