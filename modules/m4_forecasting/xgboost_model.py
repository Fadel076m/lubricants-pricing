"""XGBoost forecasting model — M4 Forecasting.

Pourquoi XGBoost ?
    Le Brent, le taux USD/XOF et l'inflation ont des effets non-linéaires
    sur les volumes et les marges. XGBoost capture ces interactions via
    des arbres de décision boostés, sans hypothèse de linéarité.
    C'est aussi le modèle le plus "explicable" via feature importance.
"""

import numpy as np
import pandas as pd
from loguru import logger
from xgboost import XGBRegressor

from ._features import engineer_lag_features, MACRO_FEATURES, LAG_PERIODS, ROLLING_WINDOWS


def _feature_cols(target: str) -> list[str]:
    lags     = [f"{target}_lag_{l}"  for l in LAG_PERIODS]
    rolling  = [f"{target}_roll_{w}" for w in ROLLING_WINDOWS]
    return MACRO_FEATURES + ["month", "quarter"] + lags + rolling


def train_xgboost(
    df_monthly: pd.DataFrame,
    target: str,
) -> tuple[XGBRegressor, list[str]]:
    """Train XGBoost with lag + macro features.

    Returns:
        Tuple (fitted model, feature_cols).
    """
    df_feat = engineer_lag_features(df_monthly, target)
    feat_cols = [c for c in _feature_cols(target) if c in df_feat.columns]

    X = df_feat[feat_cols]
    y = df_feat[target]

    model = XGBRegressor(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X, y)
    logger.info(
        "XGBoost entraîné : {} samples | cible '{}' | {} features",
        len(X), target, len(feat_cols)
    )
    return model, feat_cols


def predict_xgboost(
    model: XGBRegressor,
    df_monthly: pd.DataFrame,
    target: str,
    feat_cols: list[str],
    horizon_months: int = 3,
) -> pd.DataFrame:
    """Recursive multi-step forecast: predict 1 step, append, repeat.

    Returns:
        DataFrame with columns: ds | yhat | model
    """
    history   = df_monthly.copy()
    forecasts = []

    for step in range(horizon_months):
        df_feat = engineer_lag_features(history, target)
        if df_feat.empty:
            break
        last_row   = df_feat.tail(1)
        available  = [c for c in feat_cols if c in last_row.columns]
        X_pred     = last_row[available].reindex(columns=feat_cols, fill_value=0)
        y_hat      = float(model.predict(X_pred)[0])

        next_date  = pd.to_datetime(history["date"].iloc[-1]) + pd.DateOffset(months=1)
        new_row    = history.tail(1).copy()
        new_row["date"]  = next_date
        new_row[target]  = y_hat
        history    = pd.concat([history, new_row], ignore_index=True)
        forecasts.append({"ds": next_date, "yhat": round(y_hat, 2), "model": "xgboost"})

    return pd.DataFrame(forecasts)


def evaluate_xgboost(
    df_monthly: pd.DataFrame,
    target: str,
    n_test: int = 6,
) -> dict[str, object]:
    """Walk-forward evaluation.

    Returns:
        Dict with model, target, MAPE, RMSE, MAE.
    """
    train_df = df_monthly.iloc[:-n_test].copy()
    test_df  = df_monthly.iloc[-n_test:].copy()

    model, feat_cols = train_xgboost(train_df, target)
    forecast = predict_xgboost(model, train_df, target, feat_cols, horizon_months=n_test)

    y_true = test_df[target].values
    y_pred = forecast["yhat"].values[:len(y_true)]
    denom  = np.where(np.abs(y_true) < 1e-6, 1.0, y_true)

    mape = float(np.mean(np.abs((y_true - y_pred) / denom)) * 100)
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae  = float(np.mean(np.abs(y_true - y_pred)))

    logger.info(
        "XGBoost eval [{}] — MAPE: {:.2f}% | RMSE: {:.2f} | MAE: {:.2f}",
        target, mape, rmse, mae
    )
    return {
        "model": "xgboost", "target": target,
        "MAPE": round(mape, 4), "RMSE": round(rmse, 2), "MAE": round(mae, 2),
        "n_train": len(train_df), "n_test": n_test,
    }
