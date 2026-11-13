import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_healthcheck():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "SalesCast"

def test_stats_endpoint():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "totalDatasets" in data
    assert "totalHistoricalRevenue" in data

def test_create_dataset_and_list():
    payload = {
        "name": "Global SaaS Subscriptions",
        "description": "Monthly recurring SaaS revenue stream"
    }
    res = client.post("/api/datasets", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Global SaaS Subscriptions"
    assert data["data_points_count"] == 30

    list_res = client.get("/api/datasets")
    assert list_res.status_code == 200
    assert any(d["name"] == "Global SaaS Subscriptions" for d in list_res.json())

def test_dataset_detail_and_forecast():
    # First create dataset
    payload = {
        "name": "Retail Store Sales",
        "description": "Physical retail point-of-sale data"
    }
    res = client.post("/api/datasets", json=payload)
    ds_id = res.json()["id"]

    # Fetch detail
    detail_res = client.get(f"/api/datasets/{ds_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["records"]) == 30

    # Run forecast
    f_res = client.post(f"/api/datasets/{ds_id}/forecast", json={"horizon_days": 14, "model_type": "HOLT_LINEAR"})
    assert f_res.status_code == 200
    f_data = f_res.json()
    assert f_data["dataset_id"] == ds_id
    assert len(f_data["forecast_points"]) == 14
    assert "mape" in f_data
