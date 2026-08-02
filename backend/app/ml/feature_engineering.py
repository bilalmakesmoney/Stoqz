import pandas as pd


def is_near_holiday(date_series: pd.Series) -> pd.Series:
    def check_date(d):
        if (d.month == 12 and d.day >= 18) or (d.month == 1 and d.day <= 3):
            return 1
        if (d.month == 7 and d.day >= 1 and d.day <= 6) or (d.month == 6 and d.day >= 28):
            return 1
        if d.month == 11 and d.day >= 20 and d.day <= 30:
            return 1
        if d.month == 9 and d.day <= 8:
            return 1
        return 0
    return date_series.map(check_date)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate time-series features for demand forecasting.
    """

    df = df.copy()

    df["sale_date"] = pd.to_datetime(df["sale_date"])

    df = df.sort_values(["product_name", "sale_date"])

    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["day_of_month"] = df["sale_date"].dt.day

    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_holiday"] = is_near_holiday(df["sale_date"])

    grouped = df.groupby("product_name")["quantity_sold"]

    df["lag_1"] = grouped.shift(1)
    df["lag_7"] = grouped.shift(7)

    df["rolling_mean_3"] = grouped.transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )

    df["rolling_mean_7"] = grouped.transform(
        lambda s: s.shift(1).rolling(7, min_periods=1).mean()
    )

    df["rolling_std_7"] = grouped.transform(
        lambda s: s.shift(1).rolling(7, min_periods=2).std()
    )

    return df