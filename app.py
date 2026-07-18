"""
app.py
======
Flask web application for the Electricity Consumption Analysis project.

Routes:
  /           → Dashboard (home page with KPI cards + Tableau embed placeholder)
  /insights   → Insights page (detailed summary statistics from the database)
  /api/data   → JSON API endpoint for raw data access
"""

from flask import Flask, render_template, jsonify
from sqlalchemy import create_engine, text
import pandas as pd
import os

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "electricity_db.sqlite")
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False)


# ---------------------------------------------------------------------------
# Helper: fetch summary statistics from the database
# ---------------------------------------------------------------------------

def get_dashboard_summary() -> dict:
    """Fetch KPI metrics for the dashboard."""
    with ENGINE.connect() as conn:

        # Total national consumption
        total = conn.execute(text(
            "SELECT ROUND(SUM(Electricity_Consumption_MW), 0) FROM consumption_records"
        )).scalar()

        # Total records and unique states
        row_count = conn.execute(text("SELECT COUNT(*) FROM consumption_records")).scalar()
        state_count = conn.execute(text("SELECT COUNT(DISTINCT State) FROM consumption_records")).scalar()

        # Highest consuming state (overall)
        top_state = conn.execute(text("""
            SELECT State, ROUND(SUM(Electricity_Consumption_MW), 0) AS total
            FROM consumption_records
            GROUP BY State
            ORDER BY total DESC
            LIMIT 1
        """)).fetchone()

        # Lowest consuming state (overall)
        bottom_state = conn.execute(text("""
            SELECT State, ROUND(SUM(Electricity_Consumption_MW), 0) AS total
            FROM consumption_records
            GROUP BY State
            ORDER BY total ASC
            LIMIT 1
        """)).fetchone()

        # Regional averages
        regions = conn.execute(text("""
            SELECT Region,
                   ROUND(AVG(Electricity_Consumption_MW), 2) AS avg_mw,
                   ROUND(SUM(Electricity_Consumption_MW), 0) AS total_mw
            FROM consumption_records
            GROUP BY Region
            ORDER BY total_mw DESC
        """)).fetchall()

        # Monthly national trend
        monthly_trend = conn.execute(text("""
            SELECT strftime('%Y-%m', Date) AS month,
                   ROUND(SUM(Electricity_Consumption_MW), 0) AS total_mw
            FROM consumption_records
            GROUP BY strftime('%Y-%m', Date)
            ORDER BY month
        """)).fetchall()

        # Lockdown impact: April 2019 vs April 2020
        apr_2019 = conn.execute(text("""
            SELECT ROUND(SUM(Electricity_Consumption_MW), 0)
            FROM consumption_records
            WHERE strftime('%Y-%m', Date) = '2019-04'
        """)).scalar()

        apr_2020 = conn.execute(text("""
            SELECT ROUND(SUM(Electricity_Consumption_MW), 0)
            FROM consumption_records
            WHERE strftime('%Y-%m', Date) = '2020-04'
        """)).scalar()

    lockdown_pct_drop = round((apr_2019 - apr_2020) / apr_2019 * 100, 1) if apr_2019 else 0

    return {
        "total_consumption_mw":   total,
        "record_count":           row_count,
        "state_count":            state_count,
        "top_state":              {"name": top_state[0], "total_mw": top_state[1]} if top_state else None,
        "bottom_state":           {"name": bottom_state[0], "total_mw": bottom_state[1]} if bottom_state else None,
        "regions":                [{"region": r[0], "avg_mw": r[1], "total_mw": r[2]} for r in regions],
        "monthly_trend":          [{"month": m[0], "total_mw": m[1]} for m in monthly_trend],
        "lockdown_impact": {
            "apr_2019_mw":  apr_2019,
            "apr_2020_mw":  apr_2020,
            "pct_drop":     lockdown_pct_drop,
        },
    }


def get_insights_data() -> dict:
    """Fetch detailed analytics for the insights page."""
    with ENGINE.connect() as conn:

        # Top 10 states by total consumption
        top_10 = conn.execute(text("""
            SELECT State, Region,
                   ROUND(SUM(Electricity_Consumption_MW), 0) AS total_mw,
                   ROUND(AVG(Electricity_Consumption_MW), 0) AS avg_mw
            FROM consumption_records
            GROUP BY State
            ORDER BY total_mw DESC
            LIMIT 10
        """)).fetchall()

        # Year-over-year comparison by region
        yoy = conn.execute(text("""
            SELECT Region,
                   strftime('%Y', Date) AS year,
                   ROUND(SUM(Electricity_Consumption_MW), 0) AS total_mw
            FROM consumption_records
            GROUP BY Region, strftime('%Y', Date)
            ORDER BY Region, year
        """)).fetchall()

        # Seasonal averages (by month name across both years)
        seasonal = conn.execute(text("""
            SELECT
                CASE strftime('%m', Date)
                    WHEN '01' THEN 'January'   WHEN '02' THEN 'February'
                    WHEN '03' THEN 'March'     WHEN '04' THEN 'April'
                    WHEN '05' THEN 'May'       WHEN '06' THEN 'June'
                    WHEN '07' THEN 'July'      WHEN '08' THEN 'August'
                    WHEN '09' THEN 'September' WHEN '10' THEN 'October'
                    WHEN '11' THEN 'November'  WHEN '12' THEN 'December'
                END AS month_name,
                CAST(strftime('%m', Date) AS INTEGER) AS month_num,
                ROUND(AVG(Electricity_Consumption_MW), 2) AS avg_mw
            FROM consumption_records
            GROUP BY strftime('%m', Date)
            ORDER BY month_num
        """)).fetchall()

        # Recovery tracking: monthly totals for 2020
        recovery = conn.execute(text("""
            SELECT strftime('%Y-%m', Date) AS month,
                   Region,
                   ROUND(SUM(Electricity_Consumption_MW), 0) AS total_mw
            FROM consumption_records
            WHERE strftime('%Y', Date) = '2020'
            GROUP BY strftime('%Y-%m', Date), Region
            ORDER BY month, Region
        """)).fetchall()

        # States with fastest recovery (Dec 2020 vs Apr 2020)
        # Aggregates daily records to monthly averages first to prevent Cartesian products
        fast_recovery = conn.execute(text("""
            WITH monthly_data AS (
                SELECT State, Region, strftime('%Y-%m', Date) AS Year_Month,
                       AVG(Electricity_Consumption_MW) AS Avg_MW
                FROM consumption_records
                GROUP BY State, Region, strftime('%Y-%m', Date)
            ),
            apr AS (
                SELECT State, Region, Avg_MW AS apr_mw
                FROM monthly_data
                WHERE Year_Month = '2020-04'
            ),
            dec_data AS (
                SELECT State, Avg_MW AS dec_mw
                FROM monthly_data
                WHERE Year_Month = '2020-12'
            )
            SELECT a.State, a.Region, a.apr_mw, d.dec_mw,
                   ROUND((d.dec_mw - a.apr_mw) / a.apr_mw * 100, 1) AS recovery_pct
            FROM apr a
            JOIN dec_data d ON a.State = d.State
            ORDER BY recovery_pct DESC
            LIMIT 10
        """)).fetchall()

    return {
        "top_10_states": [
            {"state": r[0], "region": r[1], "total_mw": r[2], "avg_mw": r[3]}
            for r in top_10
        ],
        "yoy_comparison": [
            {"region": r[0], "year": r[1], "total_mw": r[2]}
            for r in yoy
        ],
        "seasonal_pattern": [
            {"month": r[0], "avg_mw": r[2]}
            for r in seasonal
        ],
        "recovery_by_region": [
            {"month": r[0], "region": r[1], "total_mw": r[2]}
            for r in recovery
        ],
        "fastest_recovery": [
            {"state": r[0], "region": r[1], "apr_mw": r[2], "dec_mw": r[3], "recovery_pct": r[4]}
            for r in fast_recovery
        ],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    """Home / Dashboard page."""
    summary = get_dashboard_summary()
    return render_template("index.html", page="dashboard", data=summary)


@app.route("/insights")
def insights():
    """Insights page with detailed statistics."""
    insights_data = get_insights_data()
    summary = get_dashboard_summary()
    return render_template("insights.html", page="insights", data=summary, insights=insights_data)


@app.route("/api/data")
def api_data():
    """JSON API endpoint for programmatic access."""
    summary = get_dashboard_summary()
    return jsonify(summary)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("[!] Database not found! Run 'python generate_data.py' first.")
        exit(1)

    print("[*] Starting Flask server...")
    print("   Dashboard:  http://127.0.0.1:5000/")
    print("   Insights:   http://127.0.0.1:5000/insights")
    print("   API:        http://127.0.0.1:5000/api/data\n")

    app.run(debug=True, port=5000)
