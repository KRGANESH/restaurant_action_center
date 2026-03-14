"""
FLOW 1 - DETERMINISTIC (Rules-Based)
======================================
3 aggregate SQL rules over 100 days of data:

Rule 1 - Reorder Discipline Issues
        How often was each item at/below reorder level?
        Alert if Pct_Days_Low >= 2%

Rule 2 - Estimated Total Waste Cost
        Total money lost to waste over 100 days.
        Alert if Est_Total_Waste_Value > 500

Rule 3 - Stockout Frequency Risk
        How often did stock drop below lead time coverage?
        Alert if Pct_Days_Stockout_Risk >= 5%
"""
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


def get_reorder_discipline():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            Item_Name,
            Category,
            COUNT(*) AS Total_Days,
            SUM(CASE WHEN Current_Stock <= Reorder_Level THEN 1 ELSE 0 END) AS Days_At_Or_Below_Reorder,
            ROUND(
                100.0 * SUM(CASE WHEN Current_Stock <= Reorder_Level THEN 1 ELSE 0 END) / COUNT(*),
            1) AS Pct_Days_Low,
            ROUND(AVG(Current_Stock), 2) AS Avg_Stock_Over_Period,
            Supplier_Name,
            'Reorder Discipline Issue' AS Alert_Type
        FROM inventory
        GROUP BY Item_ID, Item_Name, Category, Supplier_Name
        HAVING Pct_Days_Low >= 2
        ORDER BY Pct_Days_Low DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [
        {
            "item": r[0], "category": r[1], "total_days": r[2],
            "days_low": r[3], "pct_days_low": r[4],
            "avg_stock": r[5], "supplier": r[6], "alert_type": r[7]
        }
        for r in rows
    ]


def get_waste_cost():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            Item_Name,
            Unit,
            ROUND(AVG(Waste_Percentage), 2) AS Avg_Waste_Pct,
            ROUND(AVG(Daily_Usage), 2) AS Avg_Daily_Usage,
            ROUND(AVG(Price_per_Unit), 2) AS Avg_Price,
            ROUND(
                SUM(Daily_Usage * (Waste_Percentage / 100.0) * Price_per_Unit),
            2) AS Est_Total_Waste_Value,
            'High Total Waste Cost' AS Alert_Type
        FROM inventory
        GROUP BY Item_ID, Item_Name, Unit
        HAVING Est_Total_Waste_Value > 500
        ORDER BY Est_Total_Waste_Value DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [
        {
            "item": r[0], "unit": r[1], "avg_waste_pct": r[2],
            "avg_daily_usage": r[3], "avg_price": r[4],
            "est_total_waste_value": r[5], "alert_type": r[6]
        }
        for r in rows
    ]


def get_stockout_frequency():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            Item_Name,
            Category,
            Supplier_Name,
            COUNT(*) AS Total_Days,
            SUM(CASE WHEN (Current_Stock / NULLIF(Daily_Usage, 0)) < Lead_Time THEN 1 ELSE 0 END) AS Days_At_Risk,
            ROUND(
                100.0 * SUM(CASE WHEN (Current_Stock / NULLIF(Daily_Usage, 0)) < Lead_Time THEN 1 ELSE 0 END) / COUNT(*),
            1) AS Pct_Days_Stockout_Risk,
            ROUND(AVG(Current_Stock / NULLIF(Daily_Usage, 0)), 2) AS Avg_Days_of_Stock,
            ROUND(AVG(Lead_Time), 1) AS Avg_Lead_Time,
            'Stockout Frequency Risk' AS Alert_Type
        FROM inventory
        GROUP BY Item_ID, Item_Name, Category, Supplier_Name
        HAVING Pct_Days_Stockout_Risk >= 5
        ORDER BY Pct_Days_Stockout_Risk DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [
        {
            "item": r[0], "category": r[1], "supplier": r[2],
            "total_days": r[3], "days_at_risk": r[4],
            "pct_days_stockout_risk": r[5], "avg_days_of_stock": r[6],
            "avg_lead_time": r[7], "alert_type": r[8]
        }
        for r in rows
    ]


def get_all_alerts():
    alerts = []
    alerts.extend(get_reorder_discipline())
    alerts.extend(get_waste_cost())
    alerts.extend(get_stockout_frequency())
    return alerts


def get_summary_stats():
    conn = sqlite3.connect(DB_PATH)
    stats = {}

    stats["total_items"] = conn.execute(
        "SELECT COUNT(DISTINCT Item_ID) FROM inventory"
    ).fetchone()[0]

    stats["reorder_discipline_count"] = conn.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT Item_ID FROM inventory
            GROUP BY Item_ID
            HAVING ROUND(
                100.0 * SUM(CASE WHEN Current_Stock <= Reorder_Level THEN 1 ELSE 0 END) / COUNT(*),
            1) >= 2
        )
        """
    ).fetchone()[0]

    stats["high_waste_count"] = conn.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT Item_ID FROM inventory
            GROUP BY Item_ID
            HAVING SUM(Daily_Usage * (Waste_Percentage / 100.0) * Price_per_Unit) > 500
        )
        """
    ).fetchone()[0]

    stats["stockout_risk_count"] = conn.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT Item_ID FROM inventory
            GROUP BY Item_ID
            HAVING ROUND(
                100.0 * SUM(CASE WHEN (Current_Stock / NULLIF(Daily_Usage,0)) < Lead_Time THEN 1 ELSE 0 END) / COUNT(*),
            1) >= 5
        )
        """
    ).fetchone()[0]

    conn.close()
    return stats