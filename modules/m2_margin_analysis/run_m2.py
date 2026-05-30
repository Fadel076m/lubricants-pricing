"""Pipeline runner for M2 — Margin Analysis.

Étapes :
    1. Charger  — transactions.parquet depuis data/synthetic/
    2. COGS     — décomposition 5 postes + sensibilité Brent
    3. Marges   — agrégations par SKU, canal, région, famille
    4. Alertes  — classification vert/ambre/rouge + SKUs critiques
    5. Figures  — 5 graphiques HTML interactifs

Usage :
    python -m modules.m2_margin_analysis.run_m2
    python -m modules.m2_margin_analysis.run_m2 --brent-shock 0.15
"""

import argparse
import time
from pathlib import Path

import pandas as pd
from loguru import logger

from .cogs_engine import (
    compute_cogs_breakdown,
    compute_brent_sensitivity,
    export_cogs_outputs,
)
from .margin_calculator import (
    compute_margin_by_channel,
    compute_margin_pivot_sku_canal,
    export_margin_outputs,
)
from .alerts import (
    compute_alert_summary,
    export_alert_outputs,
    get_sku_alerts,
)
from .visualizations import build_all_figures

# ── Chemins ───────────────────────────────────────────────────────────────────
_PROJECT_ROOT  = Path(__file__).resolve().parents[2]
_RAW_FILE      = _PROJECT_ROOT / "data" / "synthetic" / "transactions.parquet"
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
_FIGURES_DIR   = _PROCESSED_DIR / "figures" / "m2"


def _step(label: str) -> float:
    logger.info("=" * 58)
    logger.info("  {}", label)
    logger.info("=" * 58)
    return time.perf_counter()


def _done(t0: float, label: str) -> None:
    logger.success("  ✓ {} — {:.2f}s", label, time.perf_counter() - t0)


def run_pipeline(brent_shock_pct: float = 0.10) -> None:
    """Exécute le pipeline M2 complet.

    Args:
        brent_shock_pct: Amplitude du choc Brent simulé (défaut +10 %).
    """
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

    # ── ÉTAPE 2 — COGS ────────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 2 — Décomposition COGS")
    export_cogs_outputs(df, str(_PROCESSED_DIR))

    breakdown_df   = compute_cogs_breakdown(df)
    sensitivity_df = compute_brent_sensitivity(df, brent_shock_pct)

    logger.info("  Choc Brent simulé : {:+.0%}", brent_shock_pct)
    _done(t0, "COGS")

    # ── ÉTAPE 3 — Marges ──────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 3 — Calcul des marges")
    export_margin_outputs(df, str(_PROCESSED_DIR))

    channel_df = compute_margin_by_channel(df)
    pivot_df   = compute_margin_pivot_sku_canal(df).reset_index()
    _done(t0, "Marges")

    # ── ÉTAPE 4 — Alertes ─────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 4 — Détection des alertes")
    export_alert_outputs(df, str(_PROCESSED_DIR))

    summary    = compute_alert_summary(df)
    alerts_df  = get_sku_alerts(df)

    logger.info(
        "  Alertes — ROUGE: {:.1%} | AMBRE: {:.1%} | VERT: {:.1%}",
        summary["pct_rouge"], summary["pct_ambre"], summary["pct_vert"]
    )
    logger.info("  Canal le plus risqué   : {}", summary["canal_plus_risque"])
    logger.info("  Famille la plus risquée : {}", summary["famille_plus_risque"])
    logger.info(
        "  SKU le plus risqué      : {} ({:.1%})",
        summary["sku_plus_risque"], summary["marge_sku_plus_risque"]
    )
    _done(t0, "Alertes")

    # ── ÉTAPE 5 — Figures ─────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 5 — Génération des figures")
    _FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    figs = build_all_figures(
        breakdown_df=breakdown_df,
        channel_df=channel_df,
        pivot_df=pivot_df,
        alerts_df=alerts_df,
        sensitivity_df=sensitivity_df,
        brent_shock_pct=brent_shock_pct,
    )

    for name, fig in figs.items():
        out_path = _FIGURES_DIR / f"{name}.html"
        fig.write_html(str(out_path), include_plotlyjs="cdn", full_html=True)
        logger.info("  → {}", out_path.name)
    _done(t0, "Figures")

    # ── Rapport final ─────────────────────────────────────────────────────────
    elapsed = time.perf_counter() - pipeline_start
    logger.success("=" * 58)
    logger.success("  M2 PIPELINE COMPLET — {:.2f}s total", elapsed)
    logger.success("  Figures  : {}", _FIGURES_DIR)
    logger.success("  Parquets : {}", _PROCESSED_DIR)
    logger.success("=" * 58)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline M2 — Margin Analysis")
    parser.add_argument(
        "--brent-shock",
        type=float,
        default=0.10,
        dest="brent_shock",
        help="Amplitude du choc Brent simulé (ex: 0.15 pour +15%%, défaut 0.10)",
    )
    args = parser.parse_args()
    run_pipeline(brent_shock_pct=args.brent_shock)
