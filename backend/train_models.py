"""
RetailPilot AI - Machine Learning Model Training Script
Trains XGBoost Demand Forecasting Models on all retail sales records in the database.
"""

from pathlib import Path
import sys

# Ensure backend path is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.append(str(BACKEND_DIR))

# pyrefly: ignore [missing-import]
from app.database.database import SessionLocal, engine, Base
# pyrefly: ignore [missing-import]
from app.database.models import SaleRecord, PredictionRecord, UploadLog
# pyrefly: ignore [missing-import]
import app.database.models
# pyrefly: ignore [missing-import]
from app.api.prediction import sales_to_dataframe, generate_predictions_for_all_dates
# pyrefly: ignore [missing-import]
from app.ml.feature_engineering import build_features
# pyrefly: ignore [missing-import]
from app.ml.trainer import train_model, MIN_HISTORY_DAYS
# pyrefly: ignore [missing-import]
from app.ml.model_manager import ModelManager

Base.metadata.create_all(bind=engine)


def train_all_models():
    print("=" * 70)
    print(" RetailPilot AI - Training XGBoost Forecasting Models")
    print("=" * 70)

    db = SessionLocal()
    try:
        sales = db.query(SaleRecord).all()
        if not sales:
            print("No sales data found in the database. Please upload sales CSV data first via UI or API.")
            return

        df_all = sales_to_dataframe(sales)
        products = df_all["product_name"].unique()
        
        print(f"Total Sales Records: {len(sales)}")
        print(f"Total Products Found: {len(products)}")
        print("-" * 70)
        print(f"{'PRODUCT NAME':<26} | {'SAMPLES':<7} | {'AVG DEMAND':<10} | {'CONFIDENCE':<10} | {'STATUS'}")
        print("-" * 70)

        trained_count = 0
        for product_name in products:
            group = df_all[df_all["product_name"] == product_name].sort_values("sale_date")
            avg_demand = group["quantity_sold"].mean()
            
            if len(group) < MIN_HISTORY_DAYS:
                print(f"{product_name:<26} | {len(group):<7} | {avg_demand:<10.1f} | {'N/A':<10} | Insufficient history (<{MIN_HISTORY_DAYS} days)")
                continue

            featured = build_features(group).dropna(subset=["lag_1"])
            if len(featured) < MIN_HISTORY_DAYS:
                print(f"{product_name:<26} | {len(featured):<7} | {avg_demand:<10.1f} | {'N/A':<10} | Insufficient lag features")
                continue

            model, confidence = train_model(featured, featured["quantity_sold"])
            if model is not None:
                ModelManager.save(product_name, model, confidence)
                trained_count += 1
                print(f"{product_name:<26} | {len(featured):<7} | {avg_demand:<10.1f} | {confidence:<9.1f}% | Trained & Saved (.pkl)")

        print("-" * 70)
        print(f"Successfully trained {trained_count}/{len(products)} product models!")
        
        print("\nRe-generating demand predictions across entire timeline...")
        preds, tomorrow = generate_predictions_for_all_dates(db)
        print(f"Predictions updated in database for forecast date: {tomorrow}")
        print("=" * 70)

    except Exception as exc:
        print(f"Error during training: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    train_all_models()
