import os
import sqlite3
from backend.app.config import DB_PATH

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        data_points_count INTEGER,
        start_date TEXT,
        end_date TEXT,
        created_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_records (
        id TEXT PRIMARY KEY,
        dataset_id TEXT,
        date TEXT,
        revenue REAL,
        units_sold INTEGER,
        channel TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecast_models (
        id TEXT PRIMARY KEY,
        dataset_id TEXT,
        model_type TEXT,
        horizon_days INTEGER,
        mape REAL,
        rmse REAL,
        mae REAL,
        created_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecast_points (
        id TEXT PRIMARY KEY,
        model_id TEXT,
        date TEXT,
        predicted_revenue REAL,
        lower_bound REAL,
        upper_bound REAL
    );
    """)

    conn.commit()
    conn.close()

init_db()
