import uuid
import datetime
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.app.database import get_connection
from backend.app.schemas import (
    CreateDatasetRequest, DatasetResponse,
    ForecastRequest, ForecastResponse
)
from backend.app.engine.forecaster import TimeSeriesForecaster

router = APIRouter(prefix="/api", tags=["forecasting"])

@router.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "service": "SalesCast",
        "version": "1.0.0",
        "engine": "Holt-Winters & Linear Trend Time-Series Decomposition Forecaster"
    }

@router.get("/stats")
def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as c FROM datasets;")
    total_datasets = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM sales_records;")
    total_sales_records = cursor.fetchone()["c"]

    cursor.execute("SELECT SUM(revenue) as s FROM sales_records;")
    total_revenue_row = cursor.fetchone()["s"]
    total_revenue = round(total_revenue_row, 2) if total_revenue_row else 0.0

    cursor.execute("SELECT COUNT(*) as c FROM forecast_models;")
    total_forecasts = cursor.fetchone()["c"]

    cursor.execute("SELECT AVG(mape) as a FROM forecast_models;")
    avg_mape_row = cursor.fetchone()["a"]
    avg_mape = round(avg_mape_row, 2) if avg_mape_row else 0.0

    conn.close()

    return {
        "totalDatasets": total_datasets,
        "totalRecords": total_sales_records,
        "totalHistoricalRevenue": total_revenue,
        "totalForecastsRun": total_forecasts,
        "averageModelMAPE": avg_mape
    }

@router.get("/datasets", response_model=List[DatasetResponse])
def list_datasets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/datasets", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: CreateDatasetRequest):
    conn = get_connection()
    cursor = conn.cursor()

    dataset_id = "ds-" + str(uuid.uuid4())[:8]
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # If no records provided, seed with 30-day realistic enterprise revenue history
    records_to_insert = []
    if payload.records:
        for r in payload.records:
            records_to_insert.append((str(uuid.uuid4()), dataset_id, r.date, r.revenue, r.units_sold, r.channel))
    else:
        # Generate 30 days of synthetic seasonal sales data
        base_date = datetime.date(2026, 1, 1)
        base_revenue = 2500.0
        for i in range(30):
            d = (base_date + datetime.timedelta(days=i)).isoformat()
            # Upward trend + weekly seasonality + noise
            trend = i * 45.0
            day_of_week = (base_date + datetime.timedelta(days=i)).weekday()
            seasonality = 400.0 if day_of_week in [4, 5] else -150.0
            rev = round(base_revenue + trend + seasonality + ((i % 3) * 50), 2)
            records_to_insert.append((str(uuid.uuid4()), dataset_id, d, rev, int(rev / 50), "Omnichannel"))

    start_date = min(r[2] for r in records_to_insert)
    end_date = max(r[2] for r in records_to_insert)

    cursor.execute("""
    INSERT INTO datasets (id, name, description, data_points_count, start_date, end_date, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (dataset_id, payload.name, payload.description, len(records_to_insert), start_date, end_date, now_iso))

    cursor.executemany("""
    INSERT INTO sales_records (id, dataset_id, date, revenue, units_sold, channel)
    VALUES (?, ?, ?, ?, ?, ?);
    """, records_to_insert)

    conn.commit()
    conn.close()

    return {
        "id": dataset_id,
        "name": payload.name,
        "description": payload.description or "",
        "data_points_count": len(records_to_insert),
        "start_date": start_date,
        "end_date": end_date,
        "created_at": now_iso
    }

@router.get("/datasets/{dataset_id}")
def get_dataset_detail(dataset_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM datasets WHERE id = ?;", (dataset_id,))
    ds_row = cursor.fetchone()
    if not ds_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")

    cursor.execute("SELECT * FROM sales_records WHERE dataset_id = ? ORDER BY date ASC;", (dataset_id,))
    records = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM forecast_models WHERE dataset_id = ? ORDER BY created_at DESC LIMIT 5;", (dataset_id,))
    models = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        **dict(ds_row),
        "records": records,
        "models": models
    }

@router.post("/datasets/{dataset_id}/forecast", response_model=ForecastResponse)
def execute_forecast(dataset_id: str, payload: ForecastRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM datasets WHERE id = ?;", (dataset_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")

    cursor.execute("SELECT date, revenue FROM sales_records WHERE dataset_id = ? ORDER BY date ASC;", (dataset_id,))
    raw_records = [dict(r) for r in cursor.fetchall()]

    horizon = payload.horizon_days or 14
    model_type = payload.model_type or "HOLT_LINEAR"

    forecast_res = TimeSeriesForecaster.generate_forecast(raw_records, horizon=horizon, model_type=model_type)

    model_id = "mod-" + str(uuid.uuid4())[:8]
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    metrics = forecast_res["metrics"]

    cursor.execute("""
    INSERT INTO forecast_models (id, dataset_id, model_type, horizon_days, mape, rmse, mae, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (model_id, dataset_id, model_type, horizon, metrics["mape"], metrics["rmse"], metrics["mae"], now_iso))

    points_to_insert = [
        (str(uuid.uuid4()), model_id, p["date"], p["predicted_revenue"], p["lower_bound"], p["upper_bound"])
        for p in forecast_res["forecast_points"]
    ]

    cursor.executemany("""
    INSERT INTO forecast_points (id, model_id, date, predicted_revenue, lower_bound, upper_bound)
    VALUES (?, ?, ?, ?, ?, ?);
    """, points_to_insert)

    conn.commit()
    conn.close()

    return {
        "id": model_id,
        "dataset_id": dataset_id,
        "model_type": model_type,
        "horizon_days": horizon,
        "mape": metrics["mape"],
        "rmse": metrics["rmse"],
        "mae": metrics["mae"],
        "created_at": now_iso,
        "forecast_points": forecast_res["forecast_points"]
    }
