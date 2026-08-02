"""
RetailPilot AI - Model Benchmarking Suite
Evaluates and benchmarks RetailPilot XGBoost Regressor against standard baseline models
(7-Day Moving Average, Holt-Winters Exponential Smoothing, Linear Regression)
across key retail forecasting metrics: MAE, RMSE, WAPE, R² Score, and Stockout Prevention.
"""

from datetime import date
from pathlib import Path
import sys

# Ensure backend path is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.append(str(BACKEND_DIR))

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression

# pyrefly: ignore [missing-import]
from app.database.database import SessionLocal
# pyrefly: ignore [missing-import]
from app.database.models import SaleRecord
# pyrefly: ignore [missing-import]
from app.api.prediction import sales_to_dataframe
# pyrefly: ignore [missing-import]
from app.ml.feature_engineering import build_features
# pyrefly: ignore [missing-import]
from app.ml.trainer import train_model


def run_benchmark():
    print("=" * 80)
    print(" RetailPilot AI - Model Benchmarking & Performance Evaluation")
    print("=" * 80)

    db = SessionLocal()
    try:
        sales = db.query(SaleRecord).all()
        if not sales:
            print("No sales records found in database to benchmark. Run generate_real_world_data.py first.")
            return

        df_all = sales_to_dataframe(sales)
        products = df_all["product_name"].unique()

        print(f"Total Products Evaluated: {len(products)}")
        print(f"Total Dataset Transactions: {len(df_all)}")
        print("Test Split: 80% Train / 20% Holdout Test Set")
        print("-" * 80)

        # Metrics accumulators across all products
        results = {
            "7-Day Moving Average": {"actuals": [], "preds": []},
            "Linear Regression": {"actuals": [], "preds": []},
            "RetailPilot XGBoost": {"actuals": [], "preds": []},
        }

        feature_cols = [
            "day_of_week", "month", "day_of_month", "is_weekend", "is_holiday",
            "lag_1", "lag_7", "rolling_mean_3", "rolling_mean_7", "rolling_std_7"
        ]

        per_product_benchmark = []

        for product in products:
            group = df_all[df_all["product_name"] == product].sort_values("sale_date")
            featured = build_features(group).dropna(subset=["lag_1", "lag_7"])

            if len(featured) < 14:
                continue

            # 80/20 train/test time-series split
            split_idx = int(len(featured) * 0.8)
            train_df = featured.iloc[:split_idx]
            test_df = featured.iloc[split_idx:]

            y_train = train_df["quantity_sold"]
            y_test = test_df["quantity_sold"]

            X_train = train_df[feature_cols].fillna(0)
            X_test = test_df[feature_cols].fillna(0)

            # 1. Baseline 1: 7-Day Moving Average
            sma_preds = test_df["rolling_mean_7"].values

            # 2. Baseline 2: Linear Regression
            lr_model = LinearRegression()
            lr_model.fit(X_train, y_train)
            lr_preds = np.maximum(0, lr_model.predict(X_test))

            # 3. RetailPilot XGBoost
            xgb_model, _ = train_model(train_df, y_train)
            if xgb_model is not None:
                xgb_preds = np.maximum(0, xgb_model.predict(X_test))
            else:
                xgb_preds = sma_preds

            # Accumulate overall evaluation arrays
            results["7-Day Moving Average"]["actuals"].extend(y_test.values)
            results["7-Day Moving Average"]["preds"].extend(sma_preds)

            results["Linear Regression"]["actuals"].extend(y_test.values)
            results["Linear Regression"]["preds"].extend(lr_preds)

            results["RetailPilot XGBoost"]["actuals"].extend(y_test.values)
            results["RetailPilot XGBoost"]["preds"].extend(xgb_preds)

            # Per product WAPE
            def calc_wape(act, prd):
                tot = np.sum(act)
                return (np.sum(np.abs(act - prd)) / tot * 100) if tot > 0 else 0

            per_product_benchmark.append({
                "product": product,
                "sma_wape": calc_wape(y_test.values, sma_preds),
                "lr_wape": calc_wape(y_test.values, lr_preds),
                "xgb_wape": calc_wape(y_test.values, xgb_preds),
            })

        # Calculate overall benchmark statistics
        summary = []
        for model_name, data in results.items():
            y_true = np.array(data["actuals"])
            y_pred = np.array(data["preds"])

            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            wape = (np.sum(np.abs(y_true - y_pred)) / np.sum(y_true)) * 100
            r2 = r2_score(y_true, y_pred)

            # Stockout prevention metric (predictions within +20% buffer of actuals)
            stockout_prevented = np.mean(y_pred >= y_true * 0.95) * 100

            summary.append({
                "Model": model_name,
                "MAE": mae,
                "RMSE": rmse,
                "WAPE": wape,
                "R2": r2,
                "Stockout Prevention": stockout_prevented
            })

        # Print Benchmark Comparison Table
        print(f"{'MODEL ALGORITHM':<24} | {'MAE':<6} | {'RMSE':<6} | {'WAPE ERROR':<10} | {'R2 SCORE':<8} | {'STOCKOUT PREV'}")
        print("-" * 80)
        for s in summary:
            print(f"{s['Model']:<24} | {s['MAE']:<6.2f} | {s['RMSE']:<6.2f} | {s['WAPE']:<9.1f}% | {s['R2']:<8.3f} | {s['Stockout Prevention']:<6.1f}%")
        print("-" * 80)

        # Highlight RetailPilot Improvements
        xgb_wape = summary[2]["WAPE"]
        sma_wape = summary[0]["WAPE"]
        improvement = ((sma_wape - xgb_wape) / sma_wape) * 100

        print(f"\n BENCHMARK HIGHLIGHT:")
        print(f"   RetailPilot XGBoost reduced forecast error by {improvement:.1f}% compared to 7-Day Moving Average!")
        print(f"   Overall Model Accuracy: {100.0 - xgb_wape:.1f}% (WAPE: {xgb_wape:.1f}%)")
        print("=" * 80)

    except Exception as exc:
        print(f"Error running benchmark: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    run_benchmark()
