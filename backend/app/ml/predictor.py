from datetime import date, timedelta

import pandas as pd

# pyrefly: ignore [missing-import]
from app.services.explanation_engine import ExplanationEngine
# pyrefly: ignore [missing-import]
from app.ml.feature_engineering import build_features
# pyrefly: ignore [missing-import]
from app.ml.order_optimizer import calculate_order
# pyrefly: ignore [missing-import]
from app.ml.trainer import MIN_HISTORY_DAYS, train_model
# pyrefly: ignore [missing-import]
from app.services.risk_engine import RiskEngine
# pyrefly: ignore [missing-import]
from app.ml.model_manager import ModelManager


def check_tomorrow_holiday(d):
    if (d.month == 12 and d.day >= 18) or (d.month == 1 and d.day <= 3):
        return 1
    if (d.month == 7 and d.day >= 1 and d.day <= 6) or (d.month == 6 and d.day >= 28):
        return 1
    if d.month == 11 and d.day >= 20 and d.day <= 30:
        return 1
    if d.month == 9 and d.day <= 8:
        return 1
    return 0


def fallback_predict(history: pd.Series):
    recent = history.tail(7)
    predicted = float(recent.mean()) if len(recent) else 0.0
    mean_val = float(recent.mean()) if len(recent) else 1.0
    std_val = float(recent.std()) if len(recent) > 1 else 0.0
    cv = (std_val / mean_val) if mean_val > 0 else 0.0
    confidence = max(55.0, min(84.0, 84.0 - (cv * 20.0)))
    return predicted, confidence, "moving_average"


def predict_product(product_df, tomorrow):

    history = product_df.sort_values("sale_date")
    product_name = history.iloc[-1]["product_name"]

    # Try loading an already trained model
    saved_model = ModelManager.load(product_name)

    if saved_model is not None:

        featured = build_features(history).dropna(subset=["lag_1"])

        if len(featured) > 0:

            last = featured.iloc[-1]

            tomorrow_features = pd.DataFrame(
                [
                    {
                        "day_of_week": tomorrow.weekday(),
                        "month": tomorrow.month,
                        "day_of_month": tomorrow.day,
                        "is_weekend": 1 if tomorrow.weekday() >= 5 else 0,
                        "is_holiday": check_tomorrow_holiday(tomorrow),
                        "lag_1": last["quantity_sold"],
                        "lag_7": last["lag_7"],
                        "rolling_mean_3": last["rolling_mean_3"],
                        "rolling_mean_7": last["rolling_mean_7"],
                        "rolling_std_7": last["rolling_std_7"] or 0,
                    }
                ]
            )

            prediction = float(saved_model["model"].predict(tomorrow_features)[0])

            return max(0, prediction), saved_model["confidence"], "cached_model"

    if len(history) < MIN_HISTORY_DAYS:
        return fallback_predict(history["quantity_sold"])

    featured = build_features(history)

    featured = featured.dropna(subset=["lag_1"])

    if len(featured) < MIN_HISTORY_DAYS:
        return fallback_predict(history["quantity_sold"])

    model, confidence = train_model(
        featured,
        featured["quantity_sold"],
    )

    if model is None:
        return fallback_predict(history["quantity_sold"])

    ModelManager.save(product_name, model, confidence)

    last = featured.iloc[-1]

    tomorrow_features = pd.DataFrame(
        [
            {
                "day_of_week": tomorrow.weekday(),
                "month": tomorrow.month,
                "day_of_month": tomorrow.day,
                "is_weekend": 1 if tomorrow.weekday() >= 5 else 0,
                "is_holiday": check_tomorrow_holiday(tomorrow),
                "lag_1": last["quantity_sold"],
                "lag_7": last["lag_7"],
                "rolling_mean_3": last["rolling_mean_3"],
                "rolling_mean_7": last["rolling_mean_7"],
                "rolling_std_7": last["rolling_std_7"] or 0,
            }
        ]
    )

    prediction = float(model.predict(tomorrow_features)[0])

    return max(0, prediction), confidence, "xgboost"


def run_predictions(
    sales_df: pd.DataFrame,
    prediction_date: date | None = None,
):

    if sales_df.empty:
        return []

    tomorrow = prediction_date or (
        date.today() + timedelta(days=1)
    )

    results = []

    for product_name, group in sales_df.groupby("product_name"):

        prediction, confidence, model = predict_product(
            group,
            tomorrow,
        )

        latest = group.sort_values(
            "sale_date"
        ).iloc[-1]

        current_stock = int(
            latest.get("current_stock") or 0
        )

        reorder_point = latest.get("reorder_point")

        if pd.notna(reorder_point):
            reorder_point = int(reorder_point)
        else:
            reorder_point = None

        order = calculate_order(
            prediction,
            current_stock,
            reorder_point,
        )

        risk = RiskEngine.analyze(
            prediction,
            current_stock,
        )

        explanation = ExplanationEngine.generate(
            prediction,
            current_stock,
            confidence,
            history=group["quantity_sold"],
            date_val=tomorrow,
            product_name=product_name,
            category=latest.get("category"),
            reorder_point=reorder_point,
            model_type=model,
        )

        results.append(
            {
                "product_name": product_name,
                "sku": latest.get("sku"),
                "category": latest.get("category"),
                "predicted_demand": round(prediction, 2),
                "recommended_order": order,
                "current_stock": current_stock,
                "reorder_point": reorder_point,
                "confidence": round(confidence, 1),
                "model_type": model,
                "risk": risk["risk"],
                "risk_message": risk["message"],
                "severity": risk["severity"],
                "explanation": explanation,
            }
        )

    results.sort(
        key=lambda x: x["recommended_order"],
        reverse=True,
    )

    return results