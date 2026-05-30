"""Forecast pipeline orchestrator — M4 Forecasting.

Pourquoi ce fichier ?
    Orchestre les 3 modèles : évalue, sélectionne le meilleur par cible,
    génère les prévisions 30j/60j/90j et exporte les résultats.
    C'est le seul fichier que le dashboard (M6) et l'API (FastAPI) appellent.
"""

import time
from pathlib import Path

import pandas as pd
from loguru import logger

from ._features import build_monthly_aggregates
from .prophet_model import train_prophet, predict_prophet
from .xgboost_model import train_xgboost, predict_xgboost
from .lstm_model import train_lstm, predict_lstm, TF_AVAILABLE
from .model_comparison import compare_models, log_to_mlflow, select_best_model

HORIZONS_MONTHS  = [1, 2, 3]   # 30j / 60j / 90j sur données mensuelles
FORECAST_TARGETS = ["volume_vendu", "nsp", "marge_brute_pct"]
N_TEST           = 6


def _generate_forecast(
    df_monthly: pd.DataFrame,
    target: str,
    model_name: str,
    horizon: int,
) -> pd.DataFrame:
    """Dispatch vers le bon modèle et retourne un DataFrame de forecast."""
    if model_name == "xgboost":
        model, feat_cols = train_xgboost(df_monthly, target)
        return predict_xgboost(model, df_monthly, target, feat_cols, horizon)
    if model_name == "lstm" and TF_AVAILABLE:
        model, mean_val, std_val = train_lstm(df_monthly, target)
        return predict_lstm(model, df_monthly, target, mean_val, std_val, horizon_months=horizon)
    # Default: prophet
    model = train_prophet(df_monthly, target)
    return predict_prophet(model, df_monthly, horizon_months=horizon)


def run_forecast_pipeline(
    df: pd.DataFrame,
    horizons: list[int] = HORIZONS_MONTHS,
    n_test: int = N_TEST,
    use_mlflow: bool = True,
) -> dict[str, pd.DataFrame]:
    """Run the full M4 forecasting pipeline.

    Steps :
        1. Aggregate transactions to monthly level
        2. Walk-forward evaluation (Prophet / XGBoost / LSTM)
        3. Select best model per target
        4. Generate forecasts at 30 / 60 / 90 days
        5. Log metrics to MLflow

    Returns:
        Dict with keys :
            'monthly'   — monthly aggregated DataFrame
            'metrics'   — model comparison DataFrame (MAPE / RMSE / MAE)
            'forecasts' — combined forecasts (all targets, all horizons)
    """
    t0 = time.perf_counter()

    # ── Étape 1 — Agrégation ──────────────────────────────────────────────────
    df_monthly = build_monthly_aggregates(df)
    logger.info(
        "Agrégation : {} mois ({} → {})",
        len(df_monthly),
        df_monthly["date"].iloc[0].strftime("%Y-%m"),
        df_monthly["date"].iloc[-1].strftime("%Y-%m"),
    )

    # ── Étape 2 — Évaluation des modèles ─────────────────────────────────────
    metrics_df = compare_models(df_monthly, targets=FORECAST_TARGETS, n_test=n_test)

    # ── Étape 3 — Sélection et forecasts ─────────────────────────────────────
    horizon    = max(horizons)
    all_frames = []

    for target in FORECAST_TARGETS:
        best = select_best_model(metrics_df, target)
        fc   = _generate_forecast(df_monthly, target, best, horizon)
        fc["target"]       = target
        fc["best_model"]   = best
        fc["horizon_days"] = [(i + 1) * 30 for i in range(len(fc))]
        all_frames.append(fc)

    forecasts_df = pd.concat(all_frames, ignore_index=True)

    # ── Étape 4 — MLflow ─────────────────────────────────────────────────────
    if use_mlflow:
        log_to_mlflow(metrics_df)

    logger.success(
        "Pipeline M4 terminé en {:.2f}s — {} prévisions générées",
        time.perf_counter() - t0, len(forecasts_df)
    )
    return {"monthly": df_monthly, "metrics": metrics_df, "forecasts": forecasts_df}


def export_forecast_outputs(
    pipeline_results: dict[str, pd.DataFrame],
    output_dir: str,
) -> None:
    """Export all M4 outputs to parquet.

    Args:
        pipeline_results: Output of run_forecast_pipeline.
        output_dir: Destination folder.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pipeline_results["monthly"].to_parquet(
        out / "monthly_aggregates.parquet", index=False
    )
    pipeline_results["metrics"].to_parquet(
        out / "model_metrics.parquet", index=False
    )
    pipeline_results["forecasts"].to_parquet(
        out / "forecasts_30_60_90.parquet", index=False
    )
    logger.success("Exports M4 → {}", out)
