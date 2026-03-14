from flask import Flask, render_template, jsonify, request
from database.init_db import init_database
from logic.flow1_rules import get_all_alerts, get_summary_stats
from ai.enrichment import enrich_alert, discover_patterns
from config import MAX_ALERTS_TO_ENRICH
import os

app = Flask(__name__)

if not os.path.exists("database/restaurant.db"):
    init_database()


def get_top_alerts():
    from logic.flow1_rules import get_reorder_discipline, get_waste_cost, get_stockout_frequency

    reorder_alerts = get_reorder_discipline()
    waste_alerts = get_waste_cost()
    stockout_alerts = get_stockout_frequency()

    top_alerts = []
    if reorder_alerts:
        top_alerts.append(reorder_alerts[0])
    if waste_alerts:
        top_alerts.append(waste_alerts[0])
    if stockout_alerts:
        top_alerts.append(stockout_alerts[0])

    hero_stats = {
        "highest_waste_loss": waste_alerts[0] if waste_alerts else None,
        "most_frequent_reorder_risk": reorder_alerts[0] if reorder_alerts else None,
        "most_urgent_stockout_risk": stockout_alerts[0] if stockout_alerts else None,
    }
    return top_alerts, hero_stats


@app.route("/")
@app.route("/dashboard")
def dashboard():
    top_alerts, hero_stats = get_top_alerts()

    # Step 2: Summary stats for header cards
    stats = get_summary_stats()

    return render_template(
        "dashboard.html",
        top_alerts=top_alerts,
        stats=stats,
        hero_stats=hero_stats,
        total_alerts=len(top_alerts)
    )


@app.route("/api/alerts")
def api_alerts():
    return jsonify(get_all_alerts())


@app.route("/api/stats")
def api_stats():
    return jsonify(get_summary_stats())


@app.route("/api/enrich-alert", methods=["POST"])
def api_enrich_alert():
    alert = request.get_json(silent=True)
    if not alert:
        return jsonify({
            "status": "error",
            "advice": "We could not load AI suggestions because the alert data was missing."
        }), 400

    result = enrich_alert(alert)
    status_code = 200 if result.get("status") == "success" else 503
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(debug=True)
