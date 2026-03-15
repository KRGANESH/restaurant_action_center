from abc import ABC, abstractmethod

from config import DATABASE_BACKEND
from database.client import get_database_client


class InventoryRepository(ABC):
    @abstractmethod
    def fetch_reorder_discipline(self):
        pass

    @abstractmethod
    def fetch_waste_cost(self):
        pass

    @abstractmethod
    def fetch_stockout_frequency(self):
        pass

    @abstractmethod
    def fetch_summary_stats(self):
        pass


class SQLiteInventoryRepository(InventoryRepository):
    def fetch_reorder_discipline(self):
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
        with get_database_client() as conn:
            rows = conn.execute(query).fetchall()

        return [
            {
                "item": r[0], "category": r[1], "total_days": r[2],
                "days_low": r[3], "pct_days_low": r[4],
                "avg_stock": r[5], "supplier": r[6], "alert_type": r[7]
            }
            for r in rows
        ]

    def fetch_waste_cost(self):
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
        with get_database_client() as conn:
            rows = conn.execute(query).fetchall()

        return [
            {
                "item": r[0], "unit": r[1], "avg_waste_pct": r[2],
                "avg_daily_usage": r[3], "avg_price": r[4],
                "est_total_waste_value": r[5], "alert_type": r[6]
            }
            for r in rows
        ]

    def fetch_stockout_frequency(self):
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
        with get_database_client() as conn:
            rows = conn.execute(query).fetchall()

        return [
            {
                "item": r[0], "category": r[1], "supplier": r[2],
                "total_days": r[3], "days_at_risk": r[4],
                "pct_days_stockout_risk": r[5], "avg_days_of_stock": r[6],
                "avg_lead_time": r[7], "alert_type": r[8]
            }
            for r in rows
        ]

    def fetch_summary_stats(self):
        with get_database_client() as conn:
            return {
                "total_items": conn.execute(
                    "SELECT COUNT(DISTINCT Item_ID) FROM inventory"
                ).fetchone()[0],
                "reorder_discipline_count": conn.execute(
                    """
                    SELECT COUNT(*) FROM (
                        SELECT Item_ID FROM inventory
                        GROUP BY Item_ID
                        HAVING ROUND(
                            100.0 * SUM(CASE WHEN Current_Stock <= Reorder_Level THEN 1 ELSE 0 END) / COUNT(*),
                        1) >= 2
                    )
                    """
                ).fetchone()[0],
                "high_waste_count": conn.execute(
                    """
                    SELECT COUNT(*) FROM (
                        SELECT Item_ID FROM inventory
                        GROUP BY Item_ID
                        HAVING SUM(Daily_Usage * (Waste_Percentage / 100.0) * Price_per_Unit) > 500
                    )
                    """
                ).fetchone()[0],
                "stockout_risk_count": conn.execute(
                    """
                    SELECT COUNT(*) FROM (
                        SELECT Item_ID FROM inventory
                        GROUP BY Item_ID
                        HAVING ROUND(
                            100.0 * SUM(CASE WHEN (Current_Stock / NULLIF(Daily_Usage,0)) < Lead_Time THEN 1 ELSE 0 END) / COUNT(*),
                        1) >= 5
                    )
                    """
                ).fetchone()[0],
            }


def get_inventory_repository():
    if DATABASE_BACKEND == "sqlite":
        return SQLiteInventoryRepository()

    if DATABASE_BACKEND == "bigquery":
        raise NotImplementedError(
            "BigQuery repository is not implemented yet. Add a BigQueryInventoryRepository."
        )

    raise ValueError(f"Unsupported database backend: {DATABASE_BACKEND}")
