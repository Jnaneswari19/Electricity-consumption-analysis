"""
sql_queries.py
==============
Three scenario-specific SQL queries that can be run against the
'consumption_records' table in electricity_db.sqlite.

Each query maps to one of the three core analysis scenarios,
optimized for handling daily consumption records.
"""

from sqlalchemy import create_engine, text
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "electricity_db.sqlite")
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False)


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 1: Overall Consumption Trends
# -----------------------------------------------------------------------
# Month-by-month national totals to visualise shifts, seasonal patterns,
# and the COVID-19 lockdown crater (Mar–Jun 2020).
# ═══════════════════════════════════════════════════════════════════════════════

QUERY_SCENARIO_1 = """
SELECT
    strftime('%Y-%m', Date)                     AS Year_Month,
    ROUND(SUM(Electricity_Consumption_MW), 2)   AS Total_National_MW,
    ROUND(AVG(Electricity_Consumption_MW), 2)   AS Avg_Daily_State_MW,
    COUNT(DISTINCT State)                       AS State_Count,

    -- Flag lockdown months for easy filtering in Tableau
    CASE
        WHEN strftime('%Y-%m', Date) BETWEEN '2020-03' AND '2020-06'
            THEN 'Lockdown'
        WHEN strftime('%Y-%m', Date) BETWEEN '2020-07' AND '2020-09'
            THEN 'Unlock Phase'
        ELSE 'Normal'
    END AS Period_Label

FROM consumption_records
GROUP BY strftime('%Y-%m', Date)
ORDER BY Year_Month;
"""


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 2: Regional Variations in Demand
# -----------------------------------------------------------------------
# Compare Northern, Southern, Eastern, Western, and Northeastern regions
# on a monthly basis to expose structural demand differences.
# ═══════════════════════════════════════════════════════════════════════════════

QUERY_SCENARIO_2 = """
SELECT
    Region,
    strftime('%Y-%m', Date)                      AS Year_Month,
    ROUND(SUM(Electricity_Consumption_MW), 2)    AS Region_Total_MW,
    ROUND(AVG(Electricity_Consumption_MW), 2)    AS Region_Daily_Avg_MW,
    ROUND(MIN(Electricity_Consumption_MW), 2)    AS Region_Daily_Min_MW,
    ROUND(MAX(Electricity_Consumption_MW), 2)    AS Region_Daily_Max_MW,
    COUNT(DISTINCT State)                        AS States_In_Region

FROM consumption_records
GROUP BY Region, strftime('%Y-%m', Date)
ORDER BY Region, Year_Month;
"""


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 3: Recovery After Lockdown
# -----------------------------------------------------------------------
# Compare each state's average consumption in the deepest lockdown month (Apr 2020)
# against the same month in 2019, then track recovery through Dec 2020.
# Aggregates daily records to monthly averages first to prevent Cartesian products.
# ═══════════════════════════════════════════════════════════════════════════════

QUERY_SCENARIO_3 = """
WITH monthly_data AS (
    SELECT
        State,
        Region,
        strftime('%Y-%m', Date) AS Year_Month,
        AVG(Electricity_Consumption_MW) AS Avg_MW
    FROM consumption_records
    GROUP BY State, Region, strftime('%Y-%m', Date)
),
baseline AS (
    -- April 2019 as the pre-COVID baseline
    SELECT
        State,
        Region,
        Avg_MW AS Baseline_MW
    FROM monthly_data
    WHERE Year_Month = '2019-04'
),
lockdown AS (
    -- April 2020 as the deepest lockdown month
    SELECT
        State,
        Avg_MW AS Lockdown_MW
    FROM monthly_data
    WHERE Year_Month = '2020-04'
),
recovery AS (
    -- Monthly recovery trajectory (May 2020 – Dec 2020)
    SELECT
        State,
        Year_Month,
        Avg_MW AS Recovery_MW
    FROM monthly_data
    WHERE Year_Month BETWEEN '2020-05' AND '2020-12'
)
SELECT
    b.State,
    b.Region,
    ROUND(b.Baseline_MW, 2) AS Baseline_Avg_MW,
    ROUND(l.Lockdown_MW, 2) AS Lockdown_Avg_MW,
    ROUND((l.Lockdown_MW - b.Baseline_MW) / b.Baseline_MW * 100, 2)  AS Pct_Drop_From_Baseline,
    r.Year_Month,
    ROUND(r.Recovery_MW, 2) AS Recovery_Avg_MW,
    ROUND((r.Recovery_MW - l.Lockdown_MW) / l.Lockdown_MW * 100, 2)  AS Pct_Recovery_From_Lockdown,
    ROUND((r.Recovery_MW - b.Baseline_MW) / b.Baseline_MW * 100, 2)  AS Pct_vs_Baseline
FROM baseline b
JOIN lockdown l    ON b.State = l.State
JOIN recovery r    ON b.State = r.State
ORDER BY b.Region, b.State, r.Year_Month;
"""


# ---------------------------------------------------------------------------
# Runner – execute and print results
# ---------------------------------------------------------------------------

def run_query(label: str, sql: str):
    """Execute a query and print a preview of the results."""
    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"{'='*80}")
    with ENGINE.connect() as conn:
        df = pd.read_sql_query(text(sql), conn)
    print(df.head(20).to_string(index=False))
    print(f"\n  -> Total rows returned: {len(df)}\n")
    return df


if __name__ == "__main__":
    print("\n[SQL] Running scenario-specific SQL queries against electricity_db.sqlite\n")

    df1 = run_query("SCENARIO 1 — Overall Consumption Trends (Monthly National Totals)", QUERY_SCENARIO_1)
    df2 = run_query("SCENARIO 2 — Regional Variations in Demand", QUERY_SCENARIO_2)
    df3 = run_query("SCENARIO 3 — Recovery After Lockdown (State-Level Trajectories)", QUERY_SCENARIO_3)

    print("[OK] All 3 scenario queries executed successfully.")
