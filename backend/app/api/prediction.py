from datetime import date, datetime, timedelta

import pandas as pd
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

# pyrefly: ignore [missing-import]
from app.database.dependencies import get_db
# pyrefly: ignore [missing-import]
from app.database.models import PredictionRecord, SaleRecord
# pyrefly: ignore [missing-import]
from app.ml.predictor import run_predictions
# pyrefly: ignore [missing-import]
from app.schemas.prediction import (
    HealthResponse,
    PredictionHistoryItem,
    PredictionResponse,
    ProductPrediction,
)

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


def sales_to_dataframe(records: list[SaleRecord]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sale_date": record.sale_date,
                "product_name": record.product_name,
                "sku": record.sku,
                "category": record.category,
                "quantity_sold": record.quantity_sold,
                "current_stock": record.current_stock,
                "unit_cost": record.unit_cost,
                "reorder_point": record.reorder_point,
            }
            for record in records
        ]
    )


def generate_predictions_for_all_dates(db: Session):
    # pyrefly: ignore [missing-import]
    from sqlalchemy import func
    
    all_sales = db.query(SaleRecord).all()
    if not all_sales:
        return [], date.today() + timedelta(days=1)

    df_all = sales_to_dataframe(all_sales)
    
    distinct_dates_tuples = db.query(SaleRecord.sale_date).distinct().order_by(SaleRecord.sale_date).all()
    parsed_dates = []
    for d in distinct_dates_tuples:
        val = d[0]
        if val is not None:
            if isinstance(val, str):
                parsed_dates.append(date.fromisoformat(val))
            else:
                parsed_dates.append(val)
                
    if not parsed_dates:
        return [], date.today() + timedelta(days=1)
        
    max_d = max(parsed_dates)
    tomorrow = max_d + timedelta(days=1)
    
    target_dates = sorted(list(set(parsed_dates + [tomorrow])))
    if len(target_dates) > 21:
        target_dates = target_dates[-21:]
    batch_time = datetime.utcnow()
    
    db.query(PredictionRecord).delete()
    db.flush()

    latest_preds = []
    for target_d in target_dates:
        df_sub = df_all[df_all["sale_date"] <= target_d] if target_d <= max_d else df_all
        if df_sub.empty:
            df_sub = df_all
            
        preds = run_predictions(df_sub, prediction_date=target_d)
        if target_d == tomorrow:
            latest_preds = preds

        for pred in preds:
            db.add(PredictionRecord(
                product_name=pred["product_name"],
                sku=pred["sku"],
                category=pred["category"],
                predicted_demand=pred["predicted_demand"],
                recommended_order=pred["recommended_order"],
                current_stock=pred["current_stock"],
                confidence=pred["confidence"],
                prediction_date=target_d,
                created_at=batch_time,
                explanation=pred.get("explanation")
            ))
    db.commit()
    return latest_preds, tomorrow


@router.post(
    "",
    response_model=PredictionResponse,
)
def generate_predictions(
    db: Session = Depends(get_db),
    prediction_date: date | None = Query(
        default=None,
        description="Forecast date (defaults to day after max sales date)",
    ),
):

    sales = db.query(SaleRecord).all()

    if not sales:

        raise HTTPException(
            status_code=404,
            detail="No sales data found. Upload a CSV first.",
        )

    if prediction_date:
        dataframe = sales_to_dataframe(sales)
        predictions = run_predictions(dataframe, prediction_date=prediction_date)
        batch_time = datetime.utcnow()
        db.query(PredictionRecord).filter(PredictionRecord.prediction_date == prediction_date).delete()
        db.flush()
        for prediction in predictions:
            db.add(PredictionRecord(
                product_name=prediction["product_name"],
                sku=prediction["sku"],
                category=prediction["category"],
                predicted_demand=prediction["predicted_demand"],
                recommended_order=prediction["recommended_order"],
                current_stock=prediction["current_stock"],
                confidence=prediction["confidence"],
                prediction_date=prediction_date,
                created_at=batch_time,
                explanation=prediction.get("explanation"),
            ))
        db.commit()
        target_date = prediction_date
    else:
        predictions, target_date = generate_predictions_for_all_dates(db)

    return PredictionResponse(
        prediction_date=target_date,
        total_products=len(predictions),
        total_recommended_units=sum(
            item["recommended_order"]
            for item in predictions
        ),
        predictions=[
            ProductPrediction(**item)
            for item in predictions
        ],
    )


@router.post("/train")
def train_models_endpoint(db: Session = Depends(get_db)):
    sales = db.query(SaleRecord).all()
    if not sales:
        raise HTTPException(
            status_code=404,
            detail="No sales data found in the database. Upload a sales CSV first.",
        )
    
    # Clear old model pkl files to force fresh retraining
    from pathlib import Path
    model_dir = Path("app/ml/models")
    if model_dir.exists():
        for p in model_dir.glob("*.pkl"):
            try:
                p.unlink()
            except Exception:
                pass
                
    preds, target_date = generate_predictions_for_all_dates(db)
    products_count = db.query(SaleRecord.product_name).distinct().count()
    
    return {
        "success": True,
        "message": f"Successfully trained XGBoost models for {products_count} products.",
        "forecast_date": str(target_date),
        "total_predictions": len(preds)
    }


@router.get(
    "",
    response_model=PredictionResponse,
)
def latest_predictions(
    db: Session = Depends(get_db),
):

    latest = (
        db.query(PredictionRecord)
        .order_by(
            PredictionRecord.created_at.desc()
        )
        .first()
    )

    if latest is None:

        raise HTTPException(
            status_code=404,
            detail="No predictions found.",
        )

    batch = (
        db.query(PredictionRecord)
        .filter(
            PredictionRecord.prediction_date
            == latest.prediction_date
        )
        .filter(
            PredictionRecord.created_at
            == latest.created_at
        )
        .all()
    )

    # pyrefly: ignore [missing-import]
    from app.services.risk_engine import RiskEngine

    reorders = {r.product_name: r.reorder_point for r in db.query(SaleRecord.product_name, SaleRecord.reorder_point).distinct().all() if r.reorder_point is not None}

    predictions = []
    for item in batch:
        rp = reorders.get(item.product_name)
        risk_info = RiskEngine.analyze(item.predicted_demand, item.current_stock)
        predictions.append(
            ProductPrediction(
                product_name=item.product_name,
                sku=item.sku,
                category=item.category,
                predicted_demand=item.predicted_demand,
                recommended_order=item.recommended_order,
                current_stock=item.current_stock,
                reorder_point=rp,
                confidence=item.confidence,
                model_type="stored",
                risk=risk_info["risk"],
                risk_message=risk_info["message"],
                severity=risk_info["severity"]
            )
        )

    return PredictionResponse(
        prediction_date=latest.prediction_date,
        total_products=len(predictions),
        total_recommended_units=sum(
            prediction.recommended_order
            for prediction in predictions
        ),
        predictions=predictions,
    )


@router.get(
    "/product/{product_name}",
    response_model=ProductPrediction,
)
def product_prediction(
    product_name: str,
    db: Session = Depends(get_db),
):

    sales = (
        db.query(SaleRecord)
        .filter(
            SaleRecord.product_name.ilike(
                f"%{product_name}%"
            )
        )
        .all()
    )

    if not sales:

        raise HTTPException(
            status_code=404,
            detail=f"No sales found for {product_name}",
        )

    exact_match = [
        sale
        for sale in sales
        if sale.product_name.lower()
        == product_name.lower()
    ]

    records = exact_match if exact_match else sales

    dataframe = sales_to_dataframe(
        records
    )

    predictions = run_predictions(
        dataframe
    )

    if not predictions:

        raise HTTPException(
            status_code=404,
            detail="Prediction failed.",
        )

    return ProductPrediction(
        **predictions[0]
    )


@router.get(
    "/history",
    response_model=list[PredictionHistoryItem],
)
def prediction_history(
    db: Session = Depends(get_db),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
):

    history = (
        db.query(PredictionRecord)
        .order_by(
            PredictionRecord.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    return history


@router.get(
    "/health",
    response_model=HealthResponse,
)
def health(
    db: Session = Depends(get_db),
):

    sales_records = (
        db.query(SaleRecord)
        .count()
    )

    products = (
        db.query(
            SaleRecord.product_name
        )
        .distinct()
        .count()
    )

    return HealthResponse(
        status="healthy",
        sales_records=sales_records,
        products=products,
    )