# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func

# pyrefly: ignore [missing-import]
from app.database.database import get_db
# pyrefly: ignore [missing-import]
from app.database.models import SaleRecord

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/sales-trend")
def sales_trend(db: Session = Depends(get_db)):

    rows = (
        db.query(
            SaleRecord.sale_date,
            func.sum(SaleRecord.quantity_sold),
        )
        .group_by(SaleRecord.sale_date)
        .order_by(SaleRecord.sale_date)
        .all()
    )

    return [
        {
            "date": str(date),
            "sales": sales,
        }
        for date, sales in rows
    ]


@router.get("/category-distribution")
def category_distribution(db: Session = Depends(get_db)):

    rows = (
        db.query(
            SaleRecord.category,
            func.sum(SaleRecord.quantity_sold),
        )
        .group_by(SaleRecord.category)
        .all()
    )

    return [
        {
            "category": category,
            "sales": sales,
        }
        for category, sales in rows
    ]


@router.get("/top-selling")
def top_selling_products(db: Session = Depends(get_db)):

    rows = (
        db.query(
            SaleRecord.product_name,
            func.sum(SaleRecord.quantity_sold).label("sales"),
        )
        .group_by(SaleRecord.product_name)
        .order_by(func.sum(SaleRecord.quantity_sold).desc())
        .limit(10)
        .all()
    )

    return [
        {
            "product": product,
            "sales": sales,
        }
        for product, sales in rows
    ]


@router.get("/inventory-status")
def inventory_status(db: Session = Depends(get_db)):
    max_date = db.query(func.max(SaleRecord.sale_date)).scalar()
    if not max_date:
        return []

    rows = (
        db.query(
            SaleRecord.product_name,
            func.max(SaleRecord.current_stock).label("current_stock"),
            func.max(SaleRecord.reorder_point).label("reorder_point"),
        )
        .filter(SaleRecord.sale_date == max_date)
        .group_by(SaleRecord.product_name)
        .all()
    )

    return [
        {
            "product": row.product_name,
            "stock": row.current_stock,
            "reorder_point": row.reorder_point,
        }
        for row in rows
    ]