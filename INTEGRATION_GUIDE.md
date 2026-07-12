# AssetFlow — OT + X-Factor Integration Guide (v2, matches your real schema)

This version is built directly against your actual `schema.sql`, `db.py`,
and `app.py`. No guessed columns or fictional imports remain.

## Key design decisions (worth knowing before you demo)

- **Your `allocations` table had no due date.** I added two nullable
  columns (`due_at`, `returned_at`) via `ALTER TABLE` — existing rows and
  your current allocation flow are untouched.
- **OT tracks allocations, not bookings.** Your `bookings` table is for
  rooms/resources (`resource_name`, free text) with no link to `assets`,
  so it can't carry per-asset overtime. `allocations` does have `asset_id`,
  so that's the real "who has this asset and is it overdue" source of truth.
- **`allocations.to_user` is a text name, not a user ID.** OT logs store
  both `holder_name` (always populated) and `user_id` (resolved from
  `assets.allocated_to`, may be NULL if that field wasn't set). Display
  `holder_name`.
- **Maintenance recency uses `maintenance.created_at`**, since there's no
  `resolved_at` column in your schema — it's really "days since last
  maintenance activity was logged," not "days since resolved." Worth
  knowing if a judge asks a precise question.
- **Risk scoring's usage-intensity factor uses `allocations` in the last
  30 days**, not bookings, for the same asset_id reason above.
- All writes call your existing `log_activity()` from `db.py`, so OT and AI
  events show up in your **Activity Logs** screen automatically — free
  integration with a screen you already built.

## 1. Database
```bash
sqlite3 backend/assetflow.db < backend/schema_additions.sql
```
Only adds two columns to `allocations` and four new tables
(`ot_logs`, `ot_settings`, `asset_risk_scores`, `ai_recommendations`).
Nothing is dropped. Re-run `seed.py` first if you haven't already built the DB.

## 2. Backend
Copy `routes/ot.py` and `routes/xfactor.py` into `backend/routes/`.

In `app.py`, alongside your existing blueprint imports:
```python
from routes.ot import ot_bp
from routes.xfactor import xfactor_bp

app.register_blueprint(ot_bp)
app.register_blueprint(xfactor_bp)
```
That's the only change needed to `app.py`.

## 3. Giving an allocation a due date
Your current allocation approval flow (`routes/allocation.py`, not shown to
me) just sets `status = 'Approved'`. It has no due-date step. Simplest
options, pick one:

- **Quick for a hackathon:** on the OT screen, let the admin pick any
  Approved allocation and call `POST /api/ot/allocations/<id>/set-due`
  with `{ "due_at": "..." }` (or omit the body for an auto +7 days).
- **Cleaner:** add a due-date field to your existing allocation approval
  form and call the same endpoint right after approval succeeds.

## 4. AI layer (optional but strongly recommended for the demo)
```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```
Without a key, `xfactor.py` still runs — it falls back to a templated
explanation. With a key, judges see real Claude-generated language, which
is the differentiator worth showing live.

## 5. Frontend
Copy `ot.html` and `xfactor.html` into `frontend/`, add nav links from
`dashboard.html` the way you already link to `audit.html` etc.

## 6. Suggested demo flow
1. **Dashboard** — pull `/api/ot/summary` into a small widget on
   `dashboard.html` for a live "3 active OT cases, ₹450 in fines" number.
2. **Allocation screen** — approve one, then set a due date a few minutes
   in the past (for demo purposes) so it's immediately overdue.
3. **Overtime Control** (`ot.html`) — click "Run OT Scan" → fine appears
   live → click Clear to show the asset returning to Available.
4. **AI Insight Engine** (`xfactor.html`) — click "Run AI Analysis" →
   Claude-generated risk explanations stream in per asset.
5. Close with `/api/xfactor/recommend-allocation` — request a category
   live and show the AI pick the lowest-risk asset with a one-line
   justification. This is your strongest closing beat.
