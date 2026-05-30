"""Pipeline runner for M4 — Forecasting.

Étapes :
    1. Charger     — transactions.parquet
    2. Agréger     — agrégation mensuelle (36 mois)
    3. Évaluer     — walk-forward Prophet / XGBoost / LSTM (6 mois holdout)
    4. Forecaster  — meilleures prévisions 30j / 60j / 90j par cible
    5. Figures     — 4 graphiques HTML
    6. MLflow      — log des métriques

Usage :
    python -m modules.m4_forecasting.run_m4
    python -m modules.m4_forecasting.run_m4 --no-mlflow
"""

import argparse
import time
from pathlib import Path

import pandas as pd
from loguru import logger

from .forecast_pipeline import run_forecast_pipeline, export_forecast_outputs
from .visualizations import build_all_figures

_PROJECT_ROOT  = Path(__file__).resolve().parents[2]
_RAW_FILE      = _PROJECT_ROOT / "data" / "synthetic" / "transactions.parquet"
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
_FIGURES_DIR   = _PROCESSED_DIR / "figures" / "m4"


def _step(label: str) -> float:
    logger.info("=" * 58)
    logger.info("  {}", label)
    logger.info("=" * 58)
    return time.perf_counter()


def _done(t0: float, label: str) -> None:
    logger.success("  ✓ {} — {:.2f}s", label, time.perf_counter() - t0)


def run_pipeline(use_mlflow: bool = True) -> None:
    pipeline_start = time.perf_counter()

    # ── ÉTAPE 1 — Chargement ──────────────────────────────────────────────────
    t0 = _step("ÉTAPE 1 — Chargement des données")
    if not _RAW_FILE.exists():
        logger.error("Fichier introuvable : {}", _RAW_FILE)
        logger.error("Lancer d'abord : python -m modules.m1_market_insights.run_m1")
        return
    df = pd.read_parquet(_RAW_FILE)
    logger.info("  {:,} transactions chargées", len(df))
    _done(t0, "Chargement")

    # ── ÉTAPES 2→5 — Pipeline ─────────────────────────────────────────────────
    t0 = _step("ÉTAPES 2→5 — Agrégation + Évaluation + Forecast")
    results = run_forecast_pipeline(df, use_mlflow=use_mlflow)
    _done(t0, "Pipeline complet")

    # ── Résumé métriques ──────────────────────────────────────────────────────
    _step("RÉSUMÉ — Meilleures métriques par cible")
    metrics = results["metrics"].dropna(subset=["MAPE"])
    for target in metrics["target"].unique():
        sub  = metrics[metrics["target"] == target].sort_values("MAPE")
        best = sub.iloc[0]
        logger.info(
            "  {:22s} → {} (MAPE {:.2f}% | RMSE {:.2f})",
            target, best["model"], best["MAPE"], best["RMSE"]
        )

    # ── Résumé forecasts ──────────────────────────────────────────────────────
    forecasts = results["forecasts"]
    logger.info("Forecasts générés :")
    for target in forecasts["target"].unique():
        fc = forecasts[forecasts["target"] == target]
        for _, row in fc.iterrows():
            logger.info(
                "  {:22s} +{}j → {:.2f}  [{}]",
                target, row["horizon_days"], row["yhat"], row["best_model"]
            )

    # ── Exports parquets ──────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 6 — Export parquets")
    export_forecast_outputs(results, str(_PROCESSED_DIR))
    _done(t0, "Exports")

    # ── Figures ───────────────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 7 — Génération des figures")
    _FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    figs = build_all_figures(
        df_monthly=results["monthly"],
        forecasts_df=results["forecasts"],
        metrics_df=results["metrics"],
    )
    for name, fig in figs.items():
        out_path = _FIGURES_DIR / f"{name}.html"
        fig.write_html(str(out_path), include_plotlyjs="cdn", full_html=True)
        logger.info("  → {}", out_path.name)
    _done(t0, "Figures")

    elapsed = time.perf_counter() - pipeline_start
    logger.success("=" * 58)
    logger.success("  M4 PIPELINE COMPLET — {:.2f}s total", elapsed)
    logger.success("  Figures  : {}", _FIGURES_DIR)
    logger.success("  Parquets : {}", _PROCESSED_DIR)
    logger.success("=" * 58)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline M4 — Forecasting")
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        dest="no_mlflow",
        help="Désactive le logging MLflow",
    )
    args = parser.parse_args()
    run_pipeline(use_mlflow=not args.no_mlflow)
