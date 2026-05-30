"""Prophet forecasting model — M4 Forecasting.

Pourquoi Prophet ?
    Les lubrifiants en Afrique de l'Ouest ont un pic de vente nov–fév
    (saison sèche, forte utilisation des véhicules). Prophet détecte
    automatiquement cette saisonnalité annuelle multiplicative — parfait
    pour un Pricing Manager qui ne veut pas régler des hyperparamètres.
"""

import numpy as np
import pandas as pd
from loguru import logger
from prophet import Prophet

from ._features import MACRO_FEATURES


def train_prophet(
    df_monthly: pd.DataFrame,
    target: str,
    use_regressors: bool = True,
) -> Prophet:
    """Train Prophet on monthly aggregated data.

    Args:
        df_monthly: Output of build_monthly_aggregates.
        target: Column to forecast ('volume_vendu', 'nsp', 'marge_brute_pct').
        use_regressors: Add macro regressors (Brent, FX, inflation).

    Returns:
        Fitted Prophet model.
    """
    cols = ["date", target] + [r for r in MACRO_FEATURES if r in df_monthly.columns]
    pdf = df_monthly[cols].rename(columns={"date": "ds", target: "y"}).copy()

    model = Prophet(
        seasonality_mode="multiplicative",
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
    )

    if use_regressors:
        for reg in MACRO_FEATURES:
            if reg in pdf.columns:
                model.add_regressor(reg)

    model.fit(pdf)
    logger.info("Prophet entraîné : {} mois | cible '{}'", len(pdf), target)
    return model


def predict_prophet(
    model: Prophet,
    df_monthly: pd.DataFrame,
    horizon_months: int = 3,
) -> pd.DataFrame:
    """Generate Prophet forecast (future regressors = last known value).

    Returns:
        DataFrame with columns: ds | yhat | yhat_lower | yhat_upper | model
    """
    last_vals = df_monthly[MACRO_FEATURES].iloc[-1].to_dict()
    past_map  = {
        reg: df_monthly.set_index("date")[reg].to_dict()
        for reg in MACRO_FEATURES
        if reg in df_monthly.columns
    }

    future = model.make_future_dataframe(periods=horizon_months, freq="MS")

    for reg in MACRO_FEATURES:
        if reg in model.extra_regressors:
            future[reg] = future["ds"].map(
                lambda d, r=reg: past_map[r].get(d, last_vals[r])
            )

    forecast = model.predict(future)
    result = (
        forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        .tail(horizon_months)
        .assign(model="prophet")
        .reset_index(drop=True)
    )
    return result


def evaluate_prophet(
    df_monthly: pd.DataFrame,
    target: str,
    n_test: int = 6,
) -> dict[str, object]:
    """Walk-forward evaluation: train on first n-n_test months, test on last n_test.

    Returns:
        Dict with model, target, MAPE, RMSE, MAE.
    """
    train_df = df_monthly.iloc[:-n_test].copy()
    test_df  = df_monthly.iloc[-n_test:].copy()

    model    = train_prophet(train_df, target)
    forecast = predict_prophet(model, train_df, horizon_months=n_test)

    y_true = test_df[target].values
    y_pred = forecast["yhat"].values[:len(y_true)]
    denom  = np.where(np.abs(y_true) < 1e-6, 1.0, y_true)

    mape = float(np.mean(np.abs((y_true - y_pred) / denom)) * 100)
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae  = float(np.mean(np.abs(y_true - y_pred)))

    logger.info(
        "Prophet eval [{}] — MAPE: {:.2f}% | RMSE: {:.2f} | MAE: {:.2f}",
        target, mape, rmse, mae
    )
    return {
        "model": "prophet", "target": target,
        "MAPE": round(mape, 4), "RMSE": round(rmse, 2), "MAE": round(mae, 2),
        "n_train": len(train_df), "n_test": n_test,
    }
