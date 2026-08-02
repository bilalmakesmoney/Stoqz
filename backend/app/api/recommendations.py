# pyrefly: ignore [missing-import]
from fastapi import APIRouter
# pyrefly: ignore [missing-import]
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

@router.get("/")
def get_recommendations():
    return {
        "success": True,
        "recommendations": RecommendationEngine.generate(),
    }