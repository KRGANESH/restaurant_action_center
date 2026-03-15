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
from database.repository import get_inventory_repository


repository = get_inventory_repository()


def get_reorder_discipline():
    return repository.fetch_reorder_discipline()


def get_waste_cost():
    return repository.fetch_waste_cost()


def get_stockout_frequency():
    return repository.fetch_stockout_frequency()


def get_all_alerts():
    alerts = []
    alerts.extend(get_reorder_discipline())
    alerts.extend(get_waste_cost())
    alerts.extend(get_stockout_frequency())
    return alerts


def get_summary_stats():
    return repository.fetch_summary_stats()
