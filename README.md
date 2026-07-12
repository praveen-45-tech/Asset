# AssetFlow

A full-stack asset management system: 10 screens, Python/Flask backend, plain HTML/CSS/JS frontend, SQLite for storage (free, zero setup, one file).

---

## 1. Project structure

```
assetflow/
├── backend/
│   ├── app.py              <- run this to start everything
│   ├── db.py                shared DB connection + activity logger
│   ├── schema.sql            table definitions (the "data model")
│   ├── seed.py               fills the DB with demo data (run once)
│   ├── requirements.txt
│   └── routes/
│       ├── auth.py           Screen 1  - login / signup
│       ├── dashboard.py      Screen 2  - overview stats
│       ├── org.py            Screen 3  - departments/categories/employees
│       ├── assets.py         Screen 4  - asset registry + directory
│       ├── allocation.py     Screen 5  - allocate / transfer
│       ├── booking.py        Screen 6  - resource booking
│       ├── maintenance.py    Screen 7  - maintenance kanban
│       ├── audit.py          Screen 8  - audit cycles
│       ├── reports.py        Screen 9  - analytics
│       └── activity.py       Screen 10 - activity feed
└── frontend/
    ├── index.html           Screen 1
    ├── dashboard.html       Screen 2
    ├── org-setup.html       Screen 3
    ├── assets.html          Screen 4
    ├── allocation.html      Screen 5
    ├── booking.html         Screen 6
    ├── maintenance.html     Screen 7
    ├── audit.html           Screen 8
    ├── reports.html         Screen 9
    ├── activity.html        Screen 10
    ├── css/style.css        shared design system (dark navy + amber "asset tag" theme)
    └── js/
        ├── api.js           shared fetch() wrapper + toast()
        └── nav.js            shared sidebar + login guard
```

**Why this structure:** Flask serves the `frontend/` folder as static files AND the API from the same process on the same port. That means:
- No separate frontend server, no CORS setup, nothing to configure.
- Every screen is a plain `.html` file you can open by clicking a sidebar link.
- Opening `http://127.0.0.1:5000/` in a browser gives you the whole app.

---

## 2. How every screen connects (the relation between the code)

```
schema.sql  --defines-->  tables
     |
     v
db.py (get_db, log_activity)  <---- imported by every routes/*.py file
     |
     v
routes/*.py  --registered in-->  app.py  --serves-->  frontend/*.html
     ^                                                      |
     |                                                      v
     |                                              js/api.js  (fetch wrapper)
     |                                                      |
     +------------------------------------------------------+
     each screen's own <script> calls api.get()/api.post() against
     the matching /api/... route, e.g. assets.html <-> routes/assets.py
```

Concretely:
- **`db.py`** is the one file every route imports (`from db import get_db, log_activity`). This is what makes all 10 screens share one consistent database instead of each screen inventing its own storage.
- **`log_activity()`** is called inside auth.py, org.py, assets.py, allocation.py, booking.py, maintenance.py and audit.py. That's *why* Screen 10 (Activity Logs) fills up automatically — it just reads what everyone else already wrote.
- **`app.py`** is the wiring diagram: it imports each blueprint (`auth_bp`, `dashboard_bp`, ...) and calls `app.register_blueprint(...)`. If you add an 11th screen, you'd add its route file here the same way.
- **`js/nav.js`**'s `requireAuth()` runs at the top of every screen except the login page. It calls `GET /api/auth/me`; if that fails (no session cookie), it redirects to `index.html`. This is what makes screens 2–10 "protected".
- **`js/api.js`** is why no screen's JS ever writes `fetch(...)` directly — they all call `api.get(path)` / `api.post(path, body)`, which handles JSON headers, cookies, and error messages consistently.

Cross-screen business rules that are actually enforced in code (not just decoration):
- **Screen 5** blocks a second direct allocation and forces a transfer request (`routes/allocation.py`).
- **Screen 6** checks for overlapping time slots before booking (`routes/booking.py`).
- **Screen 7** moving a card to "Approved" sets the linked asset's status to `Maintenance`; moving it to "Resolved" sets it back to `Available` (`routes/maintenance.py`).
- **Screen 8**'s flagged count is a live `COUNT(*)` query over `audit_items`, not a hardcoded number (`routes/audit.py`).
- **Screen 3** editing a department is read by both Screen 4's department filter and Screen 9's utilization-by-department chart, because they all query the same `departments` table.

---

## 3. Setup - step by step (do this once)

You need **Python 3.9+** installed. Check with:
```bash
python3 --version
```

1. Open the `assetflow` folder in **VS Code** (File → Open Folder).
2. Open a terminal in VS Code (`` Ctrl+` `` / `` Cmd+` ``).
3. Go into the backend folder and install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
   *(If you're on Mac/Linux and get a "break system packages" error: `pip install -r requirements.txt --break-system-packages`)*
4. Create the database with demo data (run this once, and again anytime you want to reset the demo data):
   ```bash
   python seed.py
   ```
   You should see: `Done. Log in with admin@company.com / admin123`

---

## 4. Running the app (every time you want to demo it)

```bash
cd backend
python app.py
```

You'll see:
```
* Running on http://127.0.0.1:5000
```

Open that URL in your browser. Log in with:
- **Email:** `admin@company.com`
- **Password:** `admin123`

That's it — one command, one process, both frontend and backend. To stop it, press `Ctrl+C` in the terminal.

**If port 5000 is already used** (common on Mac, AirPlay uses it): open `backend/app.py`, change `app.run(debug=True, port=5000)` to `port=5050`, and visit `http://127.0.0.1:5050/` instead.

---

## 5. Making it look/feel even more "hackathon-ready"

Things you can extend quickly since the structure is already there:
- Add a company logo image and swap the `AF` mark in `css/style.css`'s `.brand .mark`.
- Add real QR-code generation for asset tags using the `qrcode` Python package (`pip install qrcode`), rendered on `assets.html`.
- Add email/Slack notifications by calling a webhook inside `log_activity()` in `db.py` — one change, and every screen's actions notify automatically.
- Add charts with an actual charting library (the reports screen currently uses simple CSS bar charts to avoid extra dependencies — you can swap in Chart.js by adding `<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>` to `reports.html`).

---

## 6. Git workflow for hourly commits

Since the hackathon requires committing every hour, here's the fastest safe routine.

**One-time setup:**
```bash
cd assetflow
git init
echo "backend/assetflow.db
__pycache__/
*.pyc
.venv/" > .gitignore
git add .
git commit -m "Initial project scaffold: 10 screens, Flask backend, SQLite"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```
*(`assetflow.db` is git-ignored on purpose — it's regenerated by `seed.py`, so you don't want to commit a binary database file that changes every time someone tests something.)*

**Every hour after that:**
```bash
git add .
git commit -m "Screen 6: added booking conflict detection"
git push
```
Write a commit message that names the screen or feature you just touched — judges (and your own team) can skim your commit history and see steady, feature-by-feature progress, which is exactly what hackathon judges like to see.

**Suggested hourly milestones** if you want to plan the whole build around the commit cadence:
1. Hour 1 - scaffold + Screen 1 (login/signup) working end-to-end
2. Hour 2 - Screen 2 (dashboard) wired to real data
3. Hour 3 - Screen 3 (org setup)
4. Hour 4 - Screen 4 (assets directory + registration)
5. Hour 5 - Screen 5 (allocation/transfer + double-allocation rule)
6. Hour 6 - Screen 6 (booking + conflict detection)
7. Hour 7 - Screen 7 (maintenance kanban)
8. Hour 8 - Screen 8 (audit cycle)
9. Hour 9 - Screen 9 (reports)
10. Hour 10 - Screen 10 (activity log) + polish/bugfixes
11. Hour 11+ - README, demo script, deploy (see below), stretch features

---

## 7. Deploying so judges can access it without your laptop (optional but strong)

Since this is a single Flask process serving both frontend and backend, it deploys easily to a free tier:
- **Render.com** (free web service): connect your GitHub repo, set the start command to `cd backend && pip install -r requirements.txt && python seed.py && python app.py`, and set `PORT` to what Render provides (change `app.run(port=5000)` to read `os.environ.get("PORT", 5000)`).
- **Railway.app** or **PythonAnywhere** work similarly for a free Flask + SQLite app.

For a hackathon demo, keep SQLite — it's genuinely fine at this scale and "free data storage" is exactly the requirement. Don't over-engineer with a hosted database unless the judging criteria specifically reward it.

---

## 8. What to say when you present (60-90 seconds)

1. **Problem:** Teams lose track of who has which asset, double-book rooms, and can't tell what's overdue for maintenance.
2. **Solution walkthrough:** Log in → dashboard shows a live overdue-asset alert → try to re-allocate an already-allocated laptop and show the block → submit a transfer request instead → book a room and show the conflict warning → drag a maintenance ticket to Resolved and show the asset return to Available → show the audit screen's auto-generated discrepancy count → close with the reports screen's live utilization chart.
3. **Why it's solid engineering, not just UI:** every rule above (double-allocation block, booking conflicts, kanban-driven asset status, live discrepancy counts) is enforced in the backend, not just styled in the frontend — so it survives a judge trying to break it live.
