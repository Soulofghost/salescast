import pytest
from backend.app.engine.forecaster import TimeSeriesForecaster

def test_metrics_calculation():
    actual = [100.0, 110.0, 120.0, 130.0]
    predicted = [102.0, 108.0, 122.0, 128.0]
    metrics = TimeSeriesForecaster.calculate_metrics(actual, predicted)
    assert metrics["mae"] == 2.0
    assert metrics["rmse"] == 2.0
    assert metrics["mape"] > 0.0

def test_holt_linear_forecast():
    # Steadily increasing revenue series
    values = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]
    fitted, future = TimeSeriesForecaster.holt_linear_forecast(values, horizon=3)
    assert len(fitted) == 6
    assert len(future) == 3
    # Future projections should be higher than 150.0
    assert future[0] > 145.0
    assert future[2] > future[0]

def test_linear_trend_forecast():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    fitted, future = TimeSeriesForecaster.linear_trend_forecast(values, horizon=2)
    assert len(future) == 2
    assert future[0] > 50.0
    assert future[1] > future[0]

def test_generate_forecast_confidence_intervals():
    records = [
        {"date": "2026-01-01", "revenue": 1000.0},
        {"date": "2026-01-02", "revenue": 1050.0},
        {"date": "2026-01-03", "revenue": 1100.0},
        {"date": "2026-01-04", "revenue": 1120.0},
        {"date": "2026-01-05", "revenue": 1180.0}
    ]
    res = TimeSeriesForecaster.generate_forecast(records, horizon=5, model_type="HOLT_LINEAR")
    assert res["model_type"] == "HOLT_LINEAR"
    assert len(res["forecast_points"]) == 5
    first_pt = res["forecast_points"][0]
    assert first_pt["lower_bound"] <= first_pt["predicted_revenue"]
    assert first_pt["upper_bound"] >= first_pt["predicted_revenue"]
