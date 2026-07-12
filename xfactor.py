"""
X-Factor: AI Insight Engine — rewritten against your actual schema.

Note: your `bookings` table has no `asset_id` (it's for rooms/resources by
free-text `resource_name`), so it can't feed asset-level risk scoring.
Usage intensity instead comes from `allocations` (which does have
asset_id). Maintenance recency comes from `maintenance.created_at`, since
there's no separate resolved_at column.

Two layers, both demoable independently:
1. Rule-based, explainable risk scoring — always works, no API key needed.
2. Optional Claude-generated plain-English explanation layer:
     pip install anthropic
     export ANTHROPIC_API_KEY=sk-ant-...
   Falls back to a templated explanation if no key is set.
"""

import os
import json
from flask import Blueprint, jsonify, request

from db import get_db, log_activity

xfactor_bp = Blueprint("xfactor", __name__, url_prefix="/api/xfactor")

try:
    import anthropic
    _client = anthropic.Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None
except ImportError:
    _client = None


def _compute_risk(ot_count, days_since_maintenance, allocation_count_30d):
    """Transparent, tunable scoring — not a black box, which is itself a
    good talking point ('explainable AI') for judges."""
    score = 0
    factors = {}

    ot_component = min(ot_count * 8, 35)
    score += ot_component
    factors["overtime_incidents"] = ot_count

    maint_component = min((days_since_maintenance or 999) / 3, 40)
    score += maint_component
    factors["days_since_last_maintenance"] = days_since_maintenance

    usage_component = min(allocation_count_30d * 3, 25)
    score += usage_component
    factors["allocations_last_30d"] = allocation_count_30d

    score = round(min(score, 100), 1)
    if score >= 75:
        band = "CRITICAL"
    elif score >= 50:
        band = "HIGH"
    elif score >= 25:
        band = "MEDIUM"
    else:
        band = "LOW"
    return score, band, factors


def _ai_explain(asset_name, score, band, factors):
    if _client is None:
        return (
            f"{asset_name} has a {band.lower()} risk score of {score}/100 — "
            f"{factors['overtime_incidents']} overtime incident(s), "
            f"{factors['days_since_last_maintenance']} days since last maintenance activity, "
            f"and {factors['allocations_last_30d']} allocation(s) in the last 30 days."
        )
    prompt = (
        f"You are an asset management assistant. Asset '{asset_name}' has a predictive "
        f"maintenance risk score of {score}/100 (band: {band}). Contributing factors: "
        f"{json.dumps(factors)}. In 2-3 concise sentences, explain this to a non-technical "
        f"facilities manager and recommend one clear next action."
    )
    try:
        resp = _client.messages.create(
            model="claude-sonnet-4-6", max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text")
    except Exception as e:
        return f"(AI explanation unavailable: {e}) Risk score {score}/100 — {band}."


def _score_asset(db, asset):
    asset_id = asset["id"]

    ot_count = db.execute(
        "SELECT COUNT(*) c FROM ot_logs WHERE asset_id = ?", (asset_id,)
    ).fetchone()["c"]

    last_maint = db.execute(
        "SELECT julianday('now') - julianday(MAX(created_at)) AS days "
        "FROM maintenance WHERE asset_id = ?", (asset_id,)
    ).fetchone()
    days_since_maintenance = round(last_maint["days"]) if last_maint and last_maint["days"] is not None else None

    alloc_count_30d = db.execute(
        "SELECT COUNT(*) c FROM allocations WHERE asset_id = ? AND created_at >= datetime('now','-30 days')",
        (asset_id,)
    ).fetchone()["c"]

    score, band, factors = _compute_risk(ot_count, days_since_maintenance, alloc_count_30d)
    explanation = _ai_explain(asset["name"], score, band, factors)

    db.execute("""
        INSERT INTO asset_risk_scores (asset_id, risk_score, risk_band, factors_json, ai_explanation)
        VALUES (?, ?, ?, ?, ?)
    """, (asset_id, score, band, json.dumps(factors), explanation))

    return {
        "asset_id": asset_id,
        "asset_name": asset["name"],
        "asset_tag": asset["tag"],
        "risk_score": score,
        "risk_band": band,
        "factors": factors,
        "explanation": explanation,
        "ai_powered": _client is not None,
    }


@xfactor_bp.route("/risk/<int:asset_id>", methods=["GET"])
def asset_risk(asset_id):
    db = get_db()
    asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if not asset:
        db.close()
        return jsonify({"error": "asset not found"}), 404
    result = _score_asset(db, asset)
    db.commit()
    db.close()
    return jsonify(result)


@xfactor_bp.route("/risk/scan-all", methods=["POST"])
def scan_all_risk():
    """Scores every asset in one pass — wire this to a 'Run AI Analysis' button."""
    db = get_db()
    assets = db.execute("SELECT * FROM assets").fetchall()
    results = [_score_asset(db, a) for a in assets]
    db.commit()
    db.close()
    log_activity(f"AI risk analysis run on {len(results)} assets", "System")
    return jsonify(results)


@xfactor_bp.route("/recommend-allocation", methods=["POST"])
def recommend_allocation():
    """
    Body: { "category": "Electronics", "department_id": 1 }
    Recommends which available asset in that category to allocate, using the
    most recent risk score (lower = better) as the ranking signal.
    """
    payload = request.get_json(force=True) or {}
    category = payload.get("category", "")
    department_id = payload.get("department_id")

    db = get_db()
    candidates = db.execute("""
        SELECT a.*, COALESCE((
            SELECT risk_score FROM asset_risk_scores
            WHERE asset_id = a.id ORDER BY computed_at DESC LIMIT 1
        ), 0) AS risk_score
        FROM assets a
        WHERE a.status = 'Available' AND a.category = ?
        ORDER BY risk_score ASC
        LIMIT 5
    """, (category,)).fetchall()

    if not candidates:
        db.close()
        return jsonify({"error": f"No available assets in category '{category}'"}), 404

    best = candidates[0]
    reasoning = (
        f"Recommending '{best['name']}' ({best['tag']}) — lowest predictive risk score "
        f"({best['risk_score']}/100) among {len(candidates)} available {category} assets."
    )

    if _client is not None:
        try:
            prompt = (
                f"A facilities manager needs to allocate a '{category}' asset. The best "
                f"candidate by risk score is '{best['name']}' ({best['tag']}, risk "
                f"{best['risk_score']}/100). Write one confident sentence recommending "
                f"this allocation for a dashboard."
            )
            resp = _client.messages.create(
                model="claude-sonnet-4-6", max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            reasoning = "".join(b.text for b in resp.content if b.type == "text")
        except Exception:
            pass

    db.execute("""
        INSERT INTO ai_recommendations (request_context, recommendation, reasoning, confidence)
        VALUES (?, ?, ?, ?)
    """, (json.dumps(payload), f"{best['name']} ({best['tag']})", reasoning, 0.9 if _client else 0.6))
    db.commit()
    db.close()
    log_activity(f"AI recommended {best['name']} for {category} request", "System")

    return jsonify({
        "recommended_asset": dict(best),
        "reasoning": reasoning,
        "alternatives": [dict(c) for c in candidates[1:]],
        "ai_powered": _client is not None,
    })
