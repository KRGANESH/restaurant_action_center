import pandas as pd
import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, CSV_PATH


def clean_data(df):
    print("\n--- Data Cleaning & Formatting ---")
    original_rows = len(df)

    # Step 1: Standardize column names
    # strip whitespace, lowercase, replace spaces with underscores
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    print(f"✓ Standardized column names: {list(df.columns)}")

    # Step 2: Parse and format Date column
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    invalid_dates = df["Date"].isna().sum()
    if invalid_dates:
        print(f"  ⚠ {invalid_dates} rows had invalid dates — dropped")
        df = df.dropna(subset=["Date"])
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    print(f"✓ Date column parsed and formatted to YYYY-MM-DD")

    # Step 3: Strip whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()
    print(f"✓ Stripped whitespace from string columns: {list(str_cols)}")

    # Step 4: Standardize text casing
    # Item_Name and Category to Title Case, Supplier_Name to Title Case
    for col in ["Item_Name", "Category", "Subcategory", "Supplier_Name", "Unit"]:
        if col in df.columns:
            df[col] = df[col].str.title()
    print(f"✓ Standardized text casing to Title Case")

    # Step 5: Drop fully duplicate rows
    dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    print(f"✓ Removed {dupes} fully duplicate rows")

    # Step 6: Handle missing values
    numeric_cols = [
        "Current_Stock", "Reorder_Level", "Daily_Usage",
        "Lead_Time", "Price_per_Unit", "Seasonal_Factor", "Waste_Percentage"
    ]
    for col in numeric_cols:
        if col in df.columns:
            missing = df[col].isna().sum()
            if missing:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                print(f"  ⚠ {col}: filled {missing} missing values with median ({median_val})")

    # Step 7: Validate numeric ranges and clip outliers
    validations = {
        "Waste_Percentage":  (0, 100),
        "Seasonal_Factor":   (0, 10),
        "Current_Stock":     (0, None),
        "Daily_Usage":       (0, None),
        "Price_per_Unit":    (0, None),
        "Lead_Time":         (1, None),
        "Reorder_Level":     (0, None),
    }
    for col, (min_val, max_val) in validations.items():
        if col in df.columns:
            before = len(df)
            if min_val is not None:
                df = df[df[col] >= min_val]
            if max_val is not None:
                df = df[df[col] <= max_val]
            dropped = before - len(df)
            if dropped:
                print(f"  ⚠ {col}: dropped {dropped} rows outside valid range [{min_val}, {max_val}]")
    print(f"✓ Validated numeric ranges")

    # Step 8: Round numeric columns to sensible decimal places
    round_map = {
        "Current_Stock":    2,
        "Reorder_Level":    2,
        "Daily_Usage":      2,
        "Price_per_Unit":   2,
        "Seasonal_Factor":  2,
        "Waste_Percentage": 2,
        "Lead_Time":        0,
    }
    for col, decimals in round_map.items():
        if col in df.columns:
            df[col] = df[col].round(decimals)
    print(f"✓ Rounded numeric columns")

    # Step 9: Enforce correct data types
    df["Item_ID"]   = df["Item_ID"].astype(int)
    df["Lead_Time"] = df["Lead_Time"].astype(int)
    print(f"✓ Enforced data types (Item_ID→int, Lead_Time→int)")

    # Step 10: Sort by Date and Item_ID for clean storage
    df = df.sort_values(["Date", "Item_ID"]).reset_index(drop=True)
    print(f"✓ Sorted by Date and Item_ID")

    # Summary
    final_rows = len(df)
    print(f"\n✓ Cleaning complete: {original_rows} → {final_rows} rows "
          f"({original_rows - final_rows} removed)")
    print("----------------------------------\n")

    return df


def init_database():
    print("Initializing database...")

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at {CSV_PATH}")
        return False

    # Load raw CSV
    df = pd.read_csv(CSV_PATH)
    print(f"✓ Loaded {len(df)} rows from {CSV_PATH}")
    print(f"✓ Columns found: {list(df.columns)}")

    # Clean and format
    df = clean_data(df)

    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("inventory", conn, if_exists="replace", index=False)

    # Verify what was saved
    count = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
    conn.close()

    print(f"✓ Saved {count} clean rows to SQLite at {DB_PATH}")
    print("Database ready!")
    return True


if __name__ == "__main__":
    init_database()