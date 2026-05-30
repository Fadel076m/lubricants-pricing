"""Pipeline runner for M3 — Pricing Simulation Engine.

Étapes :
    1. Charger     — transactions.parquet
    2. Élasticités — calibration OLS log-log par canal (depuis M1)
    3. PI          — recommandations PI par SKU × Canal
    4. Scénarios   — A (+3%) / B (+5%) / C (inchangé) avec choc Brent
    5. Monte Carlo — P5/P50/P95 sur 500 itérations
    6. Figures     — 4 graphiques HTML interactifs

Usage :
    python -m modules.m3_simulation_engine.run_m3
    python -m modules.m3_simulation_engine.run_m3 --brent-shock 0.15 --mc-iter 1000
"""

import argparse
import time
from pathlib import Path

import pandas as pd
from loguru import logger

from .pi_calculator import compute_pi_recommendations, export_pi_outputs
from .elasticity_model import fit_elasticities
from .scenario_engine import (
    run_all_scenarios,
    run_monte_carlo,
    export_scenario_outputs,
)
from .visualizations import build_all_figures

# ── Chemins ───────────────────────────────────────────────────────────────────
_PROJECT_ROOT  = Path(__file__).resolve().parents[2]
_RAW_FILE      = _PROJECT_ROOT / "data" / "synthetic" / "transactions.parquet"
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
_FIGURES_DIR   = _PROCESSED_DIR / "figures" / "m3"


def _step(label: str) -> float:
    logger.info("=" * 58)
    logger.info("  {}", label)
    logger.info("=" * 58)
    return time.perf_counter()


def _done(t0: float, label: str) -> None:
    logger.success("  ✓ {} — {:.2f}s", label, time.perf_counter() - t0)


def run_pipeline(
    brent_shock_pct: float = 0.10,
    mc_iter: int = 500,
) -> None:
    """Exécute le pipeline M3 complet.

    Args:
        brent_shock_pct: Amplitude du choc Brent simulé (défaut +10 %).
        mc_iter: Nombre d'itérations Monte Carlo (défaut 500).
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

    # ── ÉTAPE 2 — Élasticités ─────────────────────────────────────────────────
    t0 = _step("ÉTAPE 2 — Calibration des élasticités")
    elasticities = fit_elasticities(df)
    for canal, elast in sorted(elasticities.items(), key=lambda x: x[1]):
        logger.info("  {:22s} : {:+.2f}", canal, elast)
    _done(t0, "Élasticités")

    # ── ÉTAPE 3 — Recommandations PI ─────────────────────────────────────────
    t0 = _step("ÉTAPE 3 — Recommandations PI")
    export_pi_outputs(df, str(_PROCESSED_DIR), brent_shock_pct)
    pi_df = compute_pi_recommendations(df, brent_shock_pct)

    critiques = (pi_df["urgence"] == "CRITIQUE").sum()
    elevees   = (pi_df["urgence"] == "ÉLEVÉE").sum()
    logger.info(
        "  Urgences — CRITIQUE: {} | ÉLEVÉE: {} | MODÉRÉE: {} | FAIBLE: {}",
        critiques, elevees,
        (pi_df["urgence"] == "MODÉRÉE").sum(),
        (pi_df["urgence"] == "FAIBLE").sum(),
    )
    if critiques > 0:
        top = pi_df[pi_df["urgence"] == "CRITIQUE"].head(3)
        for _, r in top.iterrows():
            logger.warning(
                "  !! CRITIQUE : {} | {} | PI requis {:+.1%}",
                r["sku_id"], r["canal"], r["pi_requis"]
            )
    _done(t0, "PI")

    # ── ÉTAPE 4 — Scénarios ───────────────────────────────────────────────────
    t0 = _step("ÉTAPE 4 — Scénarios A / B / C")
    results_df = run_all_scenarios(df, elasticities, brent_shock_pct)

    for scenario in ["A", "B", "C"]:
        sub = results_df[results_df["scenario"] == scenario]
        label = sub["scenario_label"].iloc[0]
        avg_delta_marge = sub["delta_marge_pts"].mean()
        avg_delta_vol   = sub["delta_volume_pct"].mean()
        logger.info(
            "  Scénario {} ({:12s}) : Δmarge {:+.2f}pts | Δvol {:+.1%}",
            scenario, label, avg_delta_marge * 100, avg_delta_vol
        )
    _done(t0, "Scénarios")

    # ── ÉTAPE 5 — Monte Carlo ─────────────────────────────────────────────────
    t0 = _step(f"ÉTAPE 5 — Monte Carlo ({mc_iter} itérations)")
    export_scenario_outputs(df, elasticities, str(_PROCESSED_DIR), brent_shock_pct, mc_iter)
    mc_df = run_monte_carlo(df, elasticities, brent_shock_pct, mc_iter)
    _done(t0, "Monte Carlo")

    # ── ÉTAPE 6 — Figures ─────────────────────────────────────────────────────
    t0 = _step("ÉTAPE 6 — Génération des figures")
    _FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    figs = build_all_figures(
        results_df=results_df,
        pi_df=pi_df,
        mc_df=mc_df,
    )
    for name, fig in figs.items():
        out_path = _FIGURES_DIR / f"{name}.html"
        fig.write_html(str(out_path), include_plotlyjs="cdn", full_html=True)
        logger.info("  → {}", out_path.name)
    _done(t0, "Figures")

    # ── Rapport final ─────────────────────────────────────────────────────────
    elapsed = time.perf_counter() - pipeline_start
    logger.success("=" * 58)
    logger.success("  M3 PIPELINE COMPLET — {:.2f}s total", elapsed)
    logger.success("  Figures  : {}", _FIGURES_DIR)
    logger.success("  Parquets : {}", _PROCESSED_DIR)
    logger.success("=" * 58)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline M3 — Pricing Simulation Engine")
    parser.add_argument(
        "--brent-shock", type=float, default=0.10, dest="brent_shock",
        help="Amplitude choc Brent (ex: 0.15 pour +15%%, défaut 0.10)",
    )
    parser.add_argument(
        "--mc-iter", type=int, default=500, dest="mc_iter",
        help="Nombre d'itérations Monte Carlo (défaut 500)",
    )
    args = parser.parse_args()
    run_pipeline(brent_shock_pct=args.brent_shock, mc_iter=args.mc_iter)
