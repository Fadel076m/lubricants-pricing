"""Pipeline runner for M1 — Market & Pricing Insights.

Enchaîne les 4 étapes dans l'ordre :
    1. Generate  — crée le dataset synthétique (14 400 lignes)
    2. Validate  — vérifie la qualité + affiche le résumé
    3. Analyse   — calcule les 5 KPIs et exporte les parquets
    4. Visualize — génère les 5 figures HTML interactives

Usage :
    python -m modules.m1_market_insights.run_m1
    python -m modules.m1_market_insights.run_m1 --force   # régénère même si parquet existe
"""

import argparse
import time
from pathlib import Path

import pandas as pd
from loguru import logger

from .data_generation import (
    OUTPUT_DIR,
    OUTPUT_FILE,
    generate_dataset,
    print_summary,
    validate_dataset,
)
from .analysis import (
    compute_brent_cogs_correlation,
    compute_channel_benchmark,
    compute_price_elasticity,
    compute_price_evolution,
    compute_regional_positioning,
)
from .visualizations import build_all_figures

# ── Chemins de sortie ─────────────────────────────────────────────────────────
_PROJECT_ROOT  = Path(__file__).resolve().parents[2]
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
_FIGURES_DIR   = _PROCESSED_DIR / "figures"

_BASE = str(_PROCESSED_DIR / "market_insights")
_PARQUET_PATHS = {
    "evolution":  f"{_BASE}.parquet",
    "channel":    f"{_BASE}_channel.parquet",
    "region":     f"{_BASE}_region.parquet",
    "elasticity": f"{_BASE}_elasticity.parquet",
}


# ── Helpers de logging ────────────────────────────────────────────────────────
def _step(label: str) -> float:
    logger.info("=" * 58)
    logger.info("  {}", label)
    logger.info("=" * 58)
    return time.perf_counter()


def _done(t0: float, label: str) -> None:
    logger.success("  ✓ {} terminé — {:.2f}s", label, time.perf_counter() - t0)


# ── Pipeline ──────────────────────────────────────────────────────────────────
def run_pipeline(force: bool = False) -> None:
    """Exécute le pipeline M1 complet.

    Args:
        force: Si True, régénère le dataset même si le parquet existe déjà.
    """
    pipeline_start = time.perf_counter()

    # ── ÉTAPE 1 — Génération ──────────────────────────────────────────────────
    t0 = _step("ÉTAPE 1 — Génération du dataset synthétique")
    if OUTPUT_FILE.exists() and not force:
        logger.info("  Cache trouvé — chargement depuis {}", OUTPUT_FILE.name)
        df = pd.read_parquet(OUTPUT_FILE)
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df = generate_dataset()
        df.to_parquet(OUTPUT_FILE, index=False)
        logger.info("  Sauvegardé → {}", OUTPUT_FILE)
    _done(t0, "Génération")

    # ── ÉTAPE 2 — Validation ──────────────────────────────────────────────────
    t0 = _step("ÉTAPE 2 — Validation & résumé")
    validate_dataset(df)
    print_summary(df)
    _done(t0, "Validation")

    # ── ÉTAPE 3 — Analyses ────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 3 — Calcul des KPIs")
    _PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    evolution_df  = compute_price_evolution(df)
    channel_df    = compute_channel_benchmark(df)
    region_df     = compute_regional_positioning(df)
    elasticity_df = compute_price_elasticity(df)
    r2_brent      = compute_brent_cogs_correlation(df)
    logger.info("  R² Brent vs Coût Huile Base : {:.4f}", r2_brent)

    evolution_df.to_parquet(_PARQUET_PATHS["evolution"], index=False)
    channel_df.to_parquet(_PARQUET_PATHS["channel"], index=False)
    region_df.reset_index().to_parquet(_PARQUET_PATHS["region"], index=False)
    elasticity_df.to_parquet(_PARQUET_PATHS["elasticity"], index=False)
    logger.info("  Parquets exportés → {}", _PROCESSED_DIR)
    _done(t0, "Analyses")

    # ── ÉTAPE 4 — Visualisations ──────────────────────────────────────────────
    t0 = _step("ÉTAPE 4 — Génération des figures")
    _FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    region_pivot_df = pd.read_parquet(_PARQUET_PATHS["region"])

    figs = build_all_figures(
        evolution_df=evolution_df,
        channel_df=channel_df,
        region_pivot_df=region_pivot_df,
        elasticity_df=elasticity_df,
        raw_df=df,
    )

    for name, fig in figs.items():
        out_path = _FIGURES_DIR / f"{name}.html"
        fig.write_html(str(out_path), include_plotlyjs="cdn", full_html=True)
        logger.info("  → {}", out_path.name)
    _done(t0, "Visualisations")

    # ── Rapport final ─────────────────────────────────────────────────────────
    elapsed = time.perf_counter() - pipeline_start
    logger.success("=" * 58)
    logger.success("  M1 PIPELINE COMPLET — {:.2f}s total", elapsed)
    logger.success("  Figures  : {}", _FIGURES_DIR)
    logger.success("  Parquets : {}", _PROCESSED_DIR)
    logger.success("=" * 58)


# ── Entrée CLI ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline M1 — Market & Pricing Insights"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Régénère le dataset même si le parquet existe déjà",
    )
    args = parser.parse_args()
    run_pipeline(force=args.force)
