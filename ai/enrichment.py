import google.generativeai as genai
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3-flash-preview")


def get_user_friendly_ai_error(error: Exception) -> str:
    error_text = str(error).lower()

    if "api key" in error_text or "authentication" in error_text or "permission denied" in error_text:
        return "AI suggestions are temporarily unavailable because the AI service is not configured correctly."
    if "quota" in error_text or "rate limit" in error_text or "resource exhausted" in error_text:
        return "AI suggestions are temporarily unavailable because the usage limit has been reached. Please try again later."
    if "503" in error_text or "service unavailable" in error_text or "timeout" in error_text:
        return "AI suggestions are temporarily unavailable because the AI service is not responding right now. Please try again in a few minutes."
    return "AI suggestions are temporarily unavailable right now. Please try again later."


def build_alert_prompt(role: str, context: str) -> str:
    return f"""
You are {role}.

Analyze the inventory alert data below and respond in exactly this format only:

Summary: <write exactly 1 sentence that explains the main risk using the item name and key numbers>
1. <write exactly 1 specific action>
2. <write exactly 1 specific action>
3. <write exactly 1 specific action>

Rules:
- Output exactly 4 lines total.
- The first line must start with "Summary:".
- Lines 2, 3, and 4 must start with "1.", "2.", and "3.".
- Do not add headings, labels, notes, markdown, bullets, or extra text.
- Do not write more than 1 sentence in the summary.
- Each suggestion must be short, direct, and specific to the numbers in the alert.
- Avoid generic advice like "monitor closely" or "improve operations".

Alert data:
{context}
"""


def enrich_alert(alert: dict) -> dict:
    alert_type = alert.get("alert_type", "Unknown")

    if alert_type == "Reorder Discipline Issue":
        context = f"""
Item: {alert['item']}
Category: {alert['category']}
Supplier: {alert['supplier']}
Total Days Tracked: {alert['total_days']}
Days At or Below Reorder Level: {alert['days_low']} days
Percentage of Days Running Low: {alert['pct_days_low']}%
Average Stock Over Period: {alert['avg_stock']} units
"""
        prompt = build_alert_prompt("a restaurant inventory control expert", context)
    elif alert_type == "High Total Waste Cost":
        context = f"""
Item: {alert['item']}
Unit: {alert['unit']}
Average Waste Percentage: {alert['avg_waste_pct']}%
Average Daily Usage: {alert['avg_daily_usage']} {alert['unit']}
Average Price per Unit: ${alert['avg_price']}
Estimated Total Waste Value over 100 days: ${alert['est_total_waste_value']}
"""
        prompt = build_alert_prompt("a restaurant waste control expert", context)
    elif alert_type == "Stockout Frequency Risk":
        context = f"""
Item: {alert['item']}
Category: {alert['category']}
Supplier: {alert['supplier']}
Total Days Tracked: {alert['total_days']}
Days at Stockout Risk: {alert['days_at_risk']}
Percentage of Days at Risk: {alert['pct_days_stockout_risk']}%
Average Days of Stock on Hand: {alert['avg_days_of_stock']} days
Average Supplier Lead Time: {alert['avg_lead_time']} days
"""
        prompt = build_alert_prompt("a restaurant supply chain expert", context)
    else:
        context = str(alert)
        prompt = build_alert_prompt("a restaurant operations expert", context)

    try:
        response = model.generate_content(prompt)
        return {"alert": alert, "advice": response.text, "status": "success"}
    except Exception as e:
        return {
            "alert": alert,
            "advice": get_user_friendly_ai_error(e),
            "status": "error",
        }


def discover_patterns(alerts: list) -> str:
    """
    FLOW 3 - DISCOVERY
    ==================
    Different from Flow 1 because we do not pre-define rules.
    We pass ALL alerts to the LLM and ask what patterns exist
    across them that the individual SQL rules could not see.
    """
    alert_lines = []
    for a in alerts:
        if a["alert_type"] == "Reorder Discipline Issue":
            alert_lines.append(
                f"- {a['item']} ({a['category']}): Reorder Discipline Issue — "
                f"low {a['pct_days_low']}% of days, supplier: {a['supplier']}"
            )
        elif a["alert_type"] == "High Total Waste Cost":
            alert_lines.append(
                f"- {a['item']}: High Total Waste Cost — "
                f"total waste ${a['est_total_waste_value']}, avg waste {a['avg_waste_pct']}%, "
                f"avg price ${a['avg_price']}"
            )
        elif a["alert_type"] == "Stockout Frequency Risk":
            alert_lines.append(
                f"- {a['item']} ({a['category']}): Stockout Frequency Risk — "
                f"at risk {a['pct_days_stockout_risk']}% of days, "
                f"avg stock covers {a['avg_days_of_stock']} days vs {a['avg_lead_time']} day lead time, "
                f"supplier: {a['supplier']}"
            )

    alert_text = "\n".join(alert_lines)

    prompt = f"""
You are a Senior Business Analyst reviewing 100 days of restaurant inventory alerts.

All triggered alerts across 3 rule categories:

{alert_text}

Do NOT just repeat the alerts. Find NON-OBVIOUS insights:
1. Are any items appearing in multiple alert categories? What does that mean?
2. Is there a link between supplier and stockout or waste issues?
3. Which single action would resolve the most alerts at once?
4. What does this pattern say about the restaurant overall supply chain health?
5. What is the ONE most urgent action the owner should take this week?

This is a discovery exercise. Find what the individual SQL rules could not see.
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Pattern discovery failed: {str(e)}"
