# pyrefly: ignore [missing-import]
from fastapi import APIRouter
# pyrefly: ignore [missing-import]
from app.database.database import SessionLocal
# pyrefly: ignore [missing-import]
from app.database.models import SaleRecord

router = APIRouter(
    prefix="/insights",
    tags=["Insights"],
)


@router.get("/")
def get_insights():

    db = SessionLocal()

    sales = db.query(SaleRecord).all()

    db.close()

    if not sales:
        return {
            "success": True,
            "insights": {
                "total_products": 0,
                "total_sales": 0,
                "low_stock_products": 0,
                "top_product": None,
            },
        }

    total_sales = sum(item.quantity_sold for item in sales)

    products = {}

    low_stock = 0

    for item in sales:

        products[item.product_name] = (
            products.get(item.product_name, 0)
            + item.quantity_sold
        )

        if item.current_stock <= item.reorder_point:
            low_stock += 1

    top_product = max(
        products,
        key=products.get,
    )

    return {
        "success": True,
        "insights": {
            "total_products": len(products),
            "total_sales": total_sales,
            "low_stock_products": low_stock,
            "top_product": top_product,
        },
    }


# pyrefly: ignore [missing-import]
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

@router.post("/assistant")
def chat_assistant(req: ChatRequest):
    # pyrefly: ignore [missing-import]
    from app.services.assistant_engine import AssistantEngine
    db = SessionLocal()
    try:
        result = AssistantEngine.answer_question(req.message, db)
        return {
            "success": True,
            "reply": result["reply"],
            "suggested_questions": result.get("suggested_questions", [])
        }
    finally:
        db.close()