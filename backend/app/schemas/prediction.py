from datetime import date, datetime

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ProductPrediction(BaseModel):
    product_name: str
    sku: str | None = None
    category: str | None = None
    predicted_demand: float
    recommended_order: int
    current_stock: int
    reorder_point: int | None = None
    confidence: float = Field(ge=0, le=100)
    model_type: str
    risk: str | None = None
    risk_message: str | None = None
    severity: str | None = None
    explanation: str | None = None


class PredictionResponse(BaseModel):
    prediction_date: date
    total_products: int
    total_recommended_units: int
    predictions: list[ProductPrediction]


class PredictionHistoryItem(BaseModel):
    id: int
    product_name: str
    predicted_demand: float
    recommended_order: int
    confidence: float
    prediction_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    sales_records: int
    products: int