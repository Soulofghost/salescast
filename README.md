# SalesCast - Revenue Time-Series Forecasting & Trend Decomposition

SalesCast is a financial analytics and revenue time-series forecasting platform designed for quantitative business planning. Built with Python 3.11, FastAPI, and SQLite WAL, SalesCast decomposes historical transactional data into underlying trend and seasonality components to project future cash flows with statistical confidence bounds.

## Core Capabilities
- **Time-Series Decomposition:** Decomposes revenue streams into trend, cyclical seasonality, and stochastic residuals.
- **Holt's Linear Exponential Smoothing:** Implements recursive level and trend smoothing parameters ($\alpha$, $\beta$) to track accelerating or decelerating demand trajectories.
- **Ordinary Least Squares (OLS) Linear Regression:** Trendline projections with automated slope and intercept estimation.
- **Statistical Error Evaluation:** Computes Mean Absolute Percentage Error (MAPE), Root Mean Squared Error (RMSE), and Mean Absolute Error (MAE).
- **Confidence Intervals:** Generates 90% confidence bands ($\pm 1.645 \cdot \text{RMSE}$) for projected daily and weekly revenue.

## Technology Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Pytest
- **Database:** SQLite (WAL mode)
- **Frontend:** Vanilla ES6+, Modern CSS Grid/Flexbox, Dark FinTech UI
- **DevOps:** Docker, Docker Compose, GitHub Actions CI

## Quickstart

```bash
# Clone the repository
git clone https://github.com/Soulofghost/salescast.git
cd salescast

# Install dependencies
pip install -r backend/requirements.txt

# Run test suite
pytest -v

# Run the API service
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints
- `GET /api/health` - Service health and forecasting engine status.
- `GET /api/stats` - Platform-wide statistics (datasets, records, revenue, average MAPE).
- `GET /api/datasets` - List registered sales data streams.
- `POST /api/datasets` - Register a new sales dataset with optional custom records or synthetic seeding.
- `GET /api/datasets/{id}` - Fetch dataset detail with complete historical records.
- `POST /api/datasets/{id}/forecast` - Execute time-series forecast for specified horizon (7-90 days).

## Author
Alvin MS ([@Soulofghost](https://github.com/Soulofghost))
