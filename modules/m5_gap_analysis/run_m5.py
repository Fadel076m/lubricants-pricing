"""Pipeline runner for M5 — Gap Analysis.

Étapes :
    1. Charger     — transactions.parquet + forecasts_30_60_90.parquet
    2. Calculer    — gaps global / mois / SKU / canal / région
    3. Alertes     — classification et résumé
    4. Root cause  — causes probables et recommandations
    5. Figures     — 5 graphiques HTML
    6. Rapport     — HTML (+ PDF si WeasyPrint installé)
    7. Exports     — parquets gap_*.parquet

Usage :
    python -m modules.m5_gap_analysis.run_m5
    python -m modules.m5_gap_analysis.run_m5 --month 2025-01
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
from loguru import logger

from .gap_engine import (
    compute_gap_global,
    compute_gap_by_month,
    compute_gap_by_sku,
    compute_gap_by_canal,
    compute_gap_by_region,
    export_gap_outputs,
)
from .alerts import (
    compute_alert_summary,
    get_canal_alerts,
    get_region_alerts,
    log_alert_summary,
)
from .root_cause import (
    analyze_sku_root_causes,
    analyze_canal_root_causes,
    generate_recommendations,
    get_top_critical_skus,
)
from .report_generator import build_html_report, export_report
from .visualizations import build_all_figures

_PROJECT_ROOT   = Path(__file__).resolve().parents[2]
_RAW_FILE       = _PROJECT_ROOT / "data" / "synthetic" / "transactions.parquet"
_FORECAST_FILE  = _PROJECT_ROOT / "data" / "processed" / "forecasts_30_60_90.parquet"
_PROCESSED_DIR  = _PROJECT_ROOT / "data" / "processed"
_FIGURES_DIR    = _PROCESSED_DIR / "figures" / "m5"
_REPORTS_DIR    = _PROJECT_ROOT / "reports"


def _step(label: str) -> float:
    logger.info("=" * 58)
    logger.info("  {}", label)
    logger.info("=" * 58)
    return time.perf_counter()


def _done(t0: float, label: str) -> None:
    logger.success("  ✓ {} — {:.2f}s", label, time.perf_counter() - t0)


def run_pipeline(report_month: str | None = None) -> None:
    pipeline_start = time.perf_counter()

    # ── ÉTAPE 1 — Chargement ──────────────────────────────────────────────────
    t0 = _step("ÉTAPE 1 — Chargement des données")

    if not _RAW_FILE.exists():
        logger.error("Transactions introuvables : {}", _RAW_FILE)
        logger.error("Lancer d'abord : python -m modules.m1_market_insights.run_m1")
        return

    df_raw = pd.read_parquet(_RAW_FILE)
    logger.info("  {:,} transactions chargées", len(df_raw))

    if not _FORECAST_FILE.exists():
        logger.error("Forecasts introuvables : {}", _FORECAST_FILE)
        logger.error("Lancer d'abord : python -m modules.m4_forecasting.run_m4")
        return

    forecasts_df = pd.read_parquet(_FORECAST_FILE)
    logger.info("  {:,} forecasts chargés", len(forecasts_df))
    _done(t0, "Chargement")

    # ── ÉTAPE 2 — Calcul des gaps ─────────────────────────────────────────────
    t0 = _step("ÉTAPE 2 — Calcul des gaps")
    gap_global  = compute_gap_global(df_raw, forecasts_df)
    gap_month   = compute_gap_by_month(df_raw, forecasts_df)
    gap_sku     = compute_gap_by_sku(df_raw)
    gap_canal   = compute_gap_by_canal(df_raw)
    gap_region  = compute_gap_by_region(df_raw)
    logger.info("  Gap global   : {} cibles", len(gap_global))
    logger.info("  Gap mensuel  : {} lignes", len(gap_month))
    logger.info("  Gap SKU      : {} lignes", len(gap_sku))
    logger.info("  Gap canal    : {} lignes", len(gap_canal))
    logger.info("  Gap région   : {} lignes", len(gap_region))
    _done(t0, "Gaps calculés")

    # ── ÉTAPE 3 — Alertes ─────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 3 — Classification des alertes")
    alert_summary = compute_alert_summary(gap_global)
    canal_alerts  = get_canal_alerts(gap_canal)
    region_alerts = get_region_alerts(gap_region)
    log_alert_summary(alert_summary)
    _done(t0, "Alertes")

    # ── ÉTAPE 4 — Root cause & recommandations ────────────────────────────────
    t0 = _step("ÉTAPE 4 — Analyse des causes")
    gap_sku_rc    = analyze_sku_root_causes(gap_sku, df_raw)
    gap_canal_rc  = analyze_canal_root_causes(gap_canal, df_raw)
    top_skus      = get_top_critical_skus(gap_sku_rc, n=5)
    recommendations = generate_recommendations(gap_global)

    logger.info("Recommandations générées :")
    for rec in recommendations:
        logger.info("  → {}", rec)
    _done(t0, "Root cause")

    # ── ÉTAPE 5 — Figures ─────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 5 — Génération des figures")
    _FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    figs = build_all_figures(gap_global, gap_month, gap_canal)
    for name, fig in figs.items():
        out_path = _FIGURES_DIR / f"{name}.html"
        fig.write_html(str(out_path), include_plotlyjs="cdn", full_html=True)
        logger.info("  → {}", out_path.name)
    _done(t0, "Figures")

    # ── ÉTAPE 6 — Rapport HTML/PDF ────────────────────────────────────────────
    t0 = _step("ÉTAPE 6 — Génération du rapport")
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    html = build_html_report(
        gap_global        = gap_global,
        alert_summary     = alert_summary,
        top_skus          = top_skus,
        gap_canal         = canal_alerts,
        gap_region        = region_alerts,
        recommendations   = recommendations,
        report_month      = report_month,
    )
    report_paths = export_report(html, str(_REPORTS_DIR), report_month)
    _done(t0, "Rapport")

    # ── ÉTAPE 7 — Exports parquets ────────────────────────────────────────────
    t0 = _step("ÉTAPE 7 — Export parquets")
    export_gap_outputs(
        {
            "global":  gap_global,
            "monthly": gap_month,
            "sku":     gap_sku_rc,
            "canal":   gap_canal_rc,
            "region":  gap_region,
        },
        str(_PROCESSED_DIR),
    )
    _done(t0, "Exports")

    elapsed = time.perf_counter() - pipeline_start
    logger.success("=" * 58)
    logger.success("  M5 PIPELINE COMPLET — {:.2f}s total", elapsed)
    logger.success("  Figures : {}", _FIGURES_DIR)
    logger.success("  Rapport : {}", report_paths.get("html"))
    logger.success("  Parquets: {}", _PROCESSED_DIR)
    logger.success("=" * 58)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline M5 — Gap Analysis")
    parser.add_argument(
        "--month",
        default=None,
        help="Mois du rapport au format YYYY-MM (ex: 2025-01). Défaut: mois courant.",
    )
    args = parser.parse_args()
    run_pipeline(report_month=args.month)
