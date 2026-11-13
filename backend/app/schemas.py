from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SalesRecordInput(BaseModel):
    date: str = Field(..., description="ISO 8601 Date string YYYY-MM-DD")
    revenue: float = Field(..., ge=0, description="Revenue in USD")
    units_sold: Optional[int] = Field(default=1, ge=0)
    channel: Optional[str] = Field(default="Direct")

class CreateDatasetRequest(BaseModel):
    name: str = Field(..., description="Dataset name, e.g. Q4 Global E-Commerce Sales")
    description: Optional[str] = Field(default="")
    records: Optional[List[SalesRecordInput]] = Field(default=None)

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    data_points_count: int
    start_date: Optional[str]
    end_date: Optional[str]
    created_at: str

class ForecastRequest(BaseModel):
    horizon_days: Optional[int] = Field(default=14, ge=1, le=90)
    model_type: Optional[str] = Field(default="HOLT_LINEAR", description="HOLT_LINEAR or LINEAR_TREND")

class ForecastPointItem(BaseModel):
    date: str
    predicted_revenue: float
    lower_bound: float
    upper_bound: float

class ForecastResponse(BaseModel):
    id: str
    dataset_id: str
    model_type: str
    horizon_days: int
    mape: float
    rmse: float
    mae: float
    created_at: str
    forecast_points: List[ForecastPointItem]
