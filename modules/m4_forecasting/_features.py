"""Feature engineering shared across all M4 models."""

import pandas as pd
import numpy as np

TARGETS       = ["nsp", "volume_vendu", "marge_brute_pct", "cout_huile_base"]
MACRO_FEATURES = ["prix_brent_usd", "taux_usd_local", "inflation_locale"]
LAG_PERIODS   = [1, 3, 6]
ROLLING_WINDOWS = [3, 6]


def build_monthly_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate raw transactions to one row per month.

    Returns:
        DataFrame sorted by date with columns:
            date | nsp | cout_huile_base | cogs_total | volume_vendu |
            marge_brute_pct | prix_brent_usd | taux_usd_local | inflation_locale
    """
    monthly = (
        df.groupby("date")
        .agg(
            nsp              =("nsp",              "mean"),
            cout_huile_base  =("cout_huile_base",  "mean"),
            cogs_total       =("cogs_total",       "mean"),
            volume_vendu     =("volume_vendu",     "sum"),
            marge_brute_pct  =("marge_brute_pct",  "mean"),
            prix_brent_usd   =("prix_brent_usd",   "mean"),
            taux_usd_local   =("taux_usd_local",   "mean"),
            inflation_locale =("inflation_locale", "mean"),
        )
        .reset_index()
        .sort_values("date")
    )
    monthly["date"] = pd.to_datetime(monthly["date"])
    return monthly.reset_index(drop=True)


def engineer_lag_features(
    df_monthly: pd.DataFrame,
    target: str,
    lag_periods: list[int] = LAG_PERIODS,
    rolling_windows: list[int] = ROLLING_WINDOWS,
) -> pd.DataFrame:
    """Add lag and rolling mean features for XGBoost/LSTM.

    Args:
        df_monthly: Output of build_monthly_aggregates.
        target: Column to create lags for.

    Returns:
        Copy with added columns (NaN rows dropped):
            {target}_lag_1/3/6 | {target}_roll_3/6 | month | quarter
    """
    out = df_monthly.copy()
    for lag in lag_periods:
        out[f"{target}_lag_{lag}"] = out[target].shift(lag)
    for window in rolling_windows:
        out[f"{target}_roll_{window}"] = out[target].shift(1).rolling(window).mean()
    out["month"]   = out["date"].dt.month
    out["quarter"] = out["date"].dt.quarter
    return out.dropna().reset_index(drop=True)
