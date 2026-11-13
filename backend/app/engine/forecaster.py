import math
import datetime
from typing import List, Dict, Any, Tuple

class TimeSeriesForecaster:
    @staticmethod
    def calculate_metrics(actual: List[float], predicted: List[float]) -> Dict[str, float]:
        """
        Calculates MAE, RMSE, and MAPE.
        """
        n = min(len(actual), len(predicted))
        if n == 0:
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

        mae_sum = 0.0
        mse_sum = 0.0
        mape_sum = 0.0
        valid_mape_count = 0

        for a, p in zip(actual[:n], predicted[:n]):
            err = a - p
            mae_sum += abs(err)
            mse_sum += err ** 2
            if abs(a) > 1e-5:
                mape_sum += abs(err / a)
                valid_mape_count += 1

        mae = mae_sum / n
        rmse = math.sqrt(mse_sum / n)
        mape = (mape_sum / valid_mape_count * 100.0) if valid_mape_count > 0 else 0.0

        return {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2)
        }

    @staticmethod
    def holt_linear_forecast(values: List[float], horizon: int, alpha: float = 0.4, beta: float = 0.2) -> Tuple[List[float], List[float]]:
        """
        Holt's Linear Exponential Smoothing.
        Returns (fitted_values, future_forecasts).
        """
        n = len(values)
        if n < 2:
            return values, [values[0] if values else 0.0] * horizon

        # Initial level and trend
        l = values[0]
        b = values[1] - values[0]
        fitted = [l]

        for i in range(1, n):
            val = values[i]
            prev_l = l
            l = alpha * val + (1.0 - alpha) * (prev_l + b)
            b = beta * (l - prev_l) + (1.0 - beta) * b
            fitted.append(round(l, 2))

        # Project future
        future = []
        for h in range(1, horizon + 1):
            pred = max(0.0, l + h * b)
            future.append(round(pred, 2))

        return fitted, future

    @staticmethod
    def linear_trend_forecast(values: List[float], horizon: int) -> Tuple[List[float], List[float]]:
        """
        Ordinary Least Squares Linear Trend Forecast.
        """
        n = len(values)
        if n < 2:
            return values, [values[0] if values else 0.0] * horizon

        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n

        num = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        den = sum((i - x_mean) ** 2 for i in range(n))

        slope = num / den if den != 0 else 0.0
        intercept = y_mean - slope * x_mean

        fitted = [round(max(0.0, slope * i + intercept), 2) for i in range(n)]
        future = [round(max(0.0, slope * (n + h) + intercept), 2) for h in range(horizon)]

        return fitted, future

    @staticmethod
    def generate_forecast(
        records: List[Dict[str, Any]],
        horizon: int = 14,
        model_type: str = "HOLT_LINEAR"
    ) -> Dict[str, Any]:
        """
        Generates full forecast payload with confidence bounds and evaluation metrics.
        """
        if not records:
            return {
                "model_type": model_type,
                "horizon_days": horizon,
                "metrics": {"mae": 0.0, "rmse": 0.0, "mape": 0.0},
                "forecast_points": []
            }

        sorted_records = sorted(records, key=lambda r: r["date"])
        values = [float(r["revenue"]) for r in sorted_records]
        last_date = datetime.date.fromisoformat(sorted_records[-1]["date"])

        if model_type == "LINEAR_TREND":
            fitted, future = TimeSeriesForecaster.linear_trend_forecast(values, horizon)
        else:
            fitted, future = TimeSeriesForecaster.holt_linear_forecast(values, horizon)

        metrics = TimeSeriesForecaster.calculate_metrics(values, fitted)
        error_margin = max(10.0, metrics["rmse"] * 1.645) # 90% confidence interval

        forecast_points = []
        for h, pred in enumerate(future, start=1):
            f_date = (last_date + datetime.timedelta(days=h)).isoformat()
            forecast_points.append({
                "date": f_date,
                "predicted_revenue": pred,
                "lower_bound": round(max(0.0, pred - error_margin), 2),
                "upper_bound": round(pred + error_margin, 2)
            })

        return {
            "model_type": model_type,
            "horizon_days": horizon,
            "metrics": metrics,
            "forecast_points": forecast_points
        }
