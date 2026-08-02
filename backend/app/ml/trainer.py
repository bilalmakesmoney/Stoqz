from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
# pyrefly: ignore [missing-import]
from xgboost import XGBRegressor

MIN_HISTORY_DAYS = 7


def train_model(features, target):
    feature_columns = [
        "day_of_week",
        "month",
        "day_of_month",
        "is_weekend",
        "is_holiday",
        "lag_1",
        "lag_7",
        "rolling_mean_3",
        "rolling_mean_7",
        "rolling_std_7",
    ]

    X = features[feature_columns].fillna(0)

    y = target

    if len(X) < MIN_HISTORY_DAYS:
        return None, 0.0

    if len(X) >= 14:

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            shuffle=False,
        )

    else:

        X_train = X
        X_test = X

        y_train = y
        y_test = y

    model = XGBRegressor(
        n_estimators=50,
        max_depth=4,
        learning_rate=0.1,
        objective="reg:squarederror",
        random_state=42,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    # Compute Weighted Absolute Percentage Error (WAPE)
    total_actual = float(y_test.sum())
    total_abs_error = float((y_test - predictions).abs().sum())
    wape = (total_abs_error / total_actual) if total_actual > 0 else 0.15

    # Compute target variance / volatility
    mean_val = float(y.mean())
    std_val = float(y.std()) if len(y) > 1 else 0.0
    cv = (std_val / mean_val) if mean_val > 0 else 0.0

    # Realistic confidence score calculation (80-92% for steady items, 60-78% for volatile items)
    base_confidence = 94.0 - (wape * 45.0) - (cv * 15.0)
    confidence = max(58.0, min(92.0, base_confidence))

    return model, confidence