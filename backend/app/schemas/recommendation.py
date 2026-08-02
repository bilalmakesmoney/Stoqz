# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class RecommendationResult(BaseModel):
    product_name: str
    predicted_demand: int
    recommended_order: int
    risk: str
    expected_revenue: float