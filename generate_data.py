"""
generate_data.py
================
Cleans and loads the downloaded 'Consumption.csv' dataset into an SQLite database.
Maps state and region abbreviations to full names and ensures columns match the
required schema: Date, State, Region, Electricity_Consumption_MW, Latitude, Longitude.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import declarative_base

DB_NAME = "electricity_db.sqlite"

# State and Region mapping for clean presentation
STATE_MAPPING = {
    "UP": "Uttar Pradesh",
    "MP": "Madhya Pradesh",
    "HP": "Himachal Pradesh",
    "J&K": "Jammu & Kashmir",
    "DNH": "Dadra and Nagar Haveli",
    "Pondy": "Puducherry"
}

REGION_MAPPING = {
    "NR": "Northern",
    "WR": "Western",
    "SR": "Southern",
    "ER": "Eastern",
    "NER": "Northeastern"
}

def clean_and_load_data(csv_path: str, db_path: str) -> None:
    """Read Consumption.csv, clean and rename columns, and store in SQLite."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input CSV not found at {csv_path}. Please make sure to download it first.")

    print(f"[*] Reading data from '{csv_path}'...")
    df_raw = pd.read_csv(csv_path)

    # Clean and parse columns
    print("[*] Processing columns and mappings...")
    df = pd.DataFrame()
    df['Date'] = pd.to_datetime(df_raw['Dates'], format='%d/%m/%Y').dt.date
    df['State'] = df_raw['States'].replace(STATE_MAPPING)
    df['Region'] = df_raw['Regions'].replace(REGION_MAPPING)
    df['Electricity_Consumption_MW'] = df_raw['Usage']
    df['Latitude'] = df_raw['latitude']
    df['Longitude'] = df_raw['longitude']

    # Keep required columns
    df = df[['Date', 'State', 'Region', 'Electricity_Consumption_MW', 'Latitude', 'Longitude']]

    # Sort data for clean storage
    df = df.sort_values(by=['Date', 'Region', 'State']).reset_index(drop=True)

    print(f"[OK] Processed {len(df)} records.")
    print(f"--- Date Range: {df['Date'].min()} -> {df['Date'].max()} ---")
    print(f"--- Unique States: {df['State'].nunique()} ---")
    print(f"--- Unique Regions: {df['Region'].unique().tolist()} ---")

    # Store in SQLite using SQLAlchemy
    print(f"[*] Storing into SQLite database at '{db_path}'...")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    Base = declarative_base()

    class ConsumptionRecord(Base):
        __tablename__ = "consumption_records"

        id = Column(Integer, primary_key=True, autoincrement=True)
        Date = Column(Date, nullable=False)
        State = Column(String(100), nullable=False)
        Region = Column(String(50), nullable=False)
        Electricity_Consumption_MW = Column(Float, nullable=False)
        Latitude = Column(Float)
        Longitude = Column(Float)

    # Drop and recreate table
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Bulk insert
    df.to_sql("consumption_records", con=engine, if_exists="append", index=False)
    print(f"[OK] Data stored in 'consumption_records' table successfully.")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(current_dir, "Consumption.csv")
    db_file = os.path.join(current_dir, DB_NAME)

    try:
        clean_and_load_data(csv_file, db_file)
        print("\n[DONE] Data pipeline completed successfully. SQLite database is ready!")
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
