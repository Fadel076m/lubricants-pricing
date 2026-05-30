"""Scenario engine with Monte Carlo — M3 Pricing Simulation Engine.

Pourquoi ce fichier ?
    Un Pricing Manager ne travaille pas avec un seul chiffre : il présente
    3 scénarios à la direction (PI faible / PI fort / prix inchangé) et
    quantifie l'incertitude via Monte Carlo. Ce fichier orchestre tout ça
    et produit des résultats avec intervalles de confiance P5/P50/P95.
"""

import numpy as np
import pandas as pd
from loguru import logger

from .elasticity_model import compute_volume_impact

# ── Définition des scénarios ──────────────────────────────────────────────────
SCENARIOS: dict[str, dict] = {
    "A": {"label": "PI +3%",        "pi_pct": 0.03},
    "B": {"label": "PI +5%",        "pi_pct": 0.05},
    "C": {"label": "Prix inchangé", "pi_pct": 0.00},
}


def run_single_scenario(
    df: pd.DataFrame,
    elasticities: dict[str, float],
    pi_pct: float,
    brent_shock_pct: float = 0.10,
) -> pd.DataFrame:
    """Simule l'impact d'un PI sur toutes les combinaisons SKU × Canal.

    Calcule, par rapport au baseline historique moyen :
    - Nouveau NSP après PI
    - Nouveau COGS après choc Brent
    - Nouveau volume après effet élasticité
    - Nouvelle marge brute et marge %

    Args:
        df: DataFrame des transactions brutes.
        elasticities: Dict {canal: elasticite} calibré sur les données.
        pi_pct: Price increase appliqué (ex: 0.03 pour +3 %).
        brent_shock_pct: Choc Brent simultané (ex: 0.10 pour +10 %).

    Returns:
        DataFrame par canal avec baseline + résultats du scénario.
    """
    agg = (
        df.groupby("canal")
        .agg(
            nsp_baseline        =("nsp",             "mean"),
            cogs_baseline       =("cogs_total",      "mean"),
            cout_huile_base_moy =("cout_huile_base", "mean"),
            volume_baseline     =("volume_vendu",    "sum"),
            marge_pct_baseline  =("marge_brute_pct", "mean"),
        )
        .reset_index()
    )

    rows = []
    for _, row in agg.iterrows():
        canal  = row["canal"]
        elast  = elasticities.get(canal, -1.0)

        # ── Nouveau COGS après choc Brent ──
        delta_cogs  = row["cout_huile_base_moy"] * brent_shock_pct
        cogs_new    = row["cogs_baseline"] + delta_cogs

        # ── Nouveau NSP après PI ──
        nsp_new = row["nsp_baseline"] * (1.0 + pi_pct)

        # ── Nouveau volume (élasticité) ──
        vol_new = compute_volume_impact(row["volume_baseline"], pi_pct, elast)

        # ── Nouvelles marges ──
        marge_brute_new     = nsp_new - cogs_new
        marge_pct_new       = marge_brute_new / nsp_new if nsp_new > 0 else 0.0

        # ── CA et profit (volume × marge) ──
        profit_baseline     = row["marge_pct_baseline"] * row["nsp_baseline"] * row["volume_baseline"]
        profit_new          = marge_brute_new * vol_new

        rows.append({
            "canal":               canal,
            "elasticite":          round(elast, 2),
            # Baseline
            "nsp_baseline":        round(row["nsp_baseline"], 2),
            "cogs_baseline":       round(row["cogs_baseline"], 2),
            "marge_pct_baseline":  round(row["marge_pct_baseline"], 4),
            "volume_baseline":     int(row["volume_baseline"]),
            "profit_baseline":     round(profit_baseline, 0),
            # Scénario
            "pi_pct":              pi_pct,
            "brent_shock_pct":     brent_shock_pct,
            "nsp_new":             round(nsp_new, 2),
            "cogs_new":            round(cogs_new, 2),
            "marge_pct_new":       round(marge_pct_new, 4),
            "volume_new":          int(vol_new),
            "profit_new":          round(profit_new, 0),
            # Deltas
            "delta_marge_pts":     round(marge_pct_new - row["marge_pct_baseline"], 4),
            "delta_volume_pct":    round((vol_new - row["volume_baseline"]) / row["volume_baseline"], 4),
            "delta_profit_pct":    round((profit_new - profit_baseline) / profit_baseline if profit_baseline != 0 else 0, 4),
        })

    return pd.DataFrame(rows)


def run_all_scenarios(
    df: pd.DataFrame,
    elasticities: dict[str, float],
    brent_shock_pct: float = 0.10,
) -> pd.DataFrame:
    """Exécute les scénarios A, B et C et retourne les résultats empilés.

    Args:
        df: DataFrame des transactions brutes.
        elasticities: Dict {canal: elasticite}.
        brent_shock_pct: Choc Brent simultané.

    Returns:
        DataFrame avec colonne 'scenario' (A/B/C) et 'scenario_label'.
    """
    frames = []
    for key, params in SCENARIOS.items():
        result = run_single_scenario(
            df, elasticities,
            pi_pct=params["pi_pct"],
            brent_shock_pct=brent_shock_pct,
        )
        result["scenario"]       = key
        result["scenario_label"] = params["label"]
        frames.append(result)

    combined = pd.concat(frames, ignore_index=True)
    logger.info(
        "Scénarios A/B/C calculés — {} lignes | choc Brent {:+.0%}",
        len(combined), brent_shock_pct
    )
    return combined


def run_monte_carlo(
    df: pd.DataFrame,
    elasticities: dict[str, float],
    brent_shock_pct: float = 0.10,
    n_iter: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """Monte Carlo sur les scénarios A/B/C avec incertitude COGS et élasticité.

    Sources d'incertitude :
        - Choc Brent : Normal(μ=brent_shock_pct, σ=brent_shock_pct×0.30)
        - Élasticité : Normal(μ=e, σ=0.15) par canal

    Args:
        df: DataFrame des transactions brutes.
        elasticities: Dict {canal: elasticite} calibré.
        brent_shock_pct: Choc Brent central.
        n_iter: Nombre d'itérations Monte Carlo (défaut 500).
        seed: Graine aléatoire pour reproductibilité.

    Returns:
        DataFrame par scénario × canal avec :
            marge_p5 | marge_p50 | marge_p95 |
            volume_p5 | volume_p50 | volume_p95 |
            profit_p5 | profit_p50 | profit_p95
    """
    rng = np.random.default_rng(seed)

    agg = (
        df.groupby("canal")
        .agg(
            nsp_baseline        =("nsp",             "mean"),
            cogs_baseline       =("cogs_total",      "mean"),
            cout_huile_base_moy =("cout_huile_base", "mean"),
            volume_baseline     =("volume_vendu",    "sum"),
            marge_pct_baseline  =("marge_brute_pct", "mean"),
        )
        .reset_index()
    )

    records = []

    for scenario_key, params in SCENARIOS.items():
        pi_pct = params["pi_pct"]

        # Distributions des paramètres incertains
        brent_samples = rng.normal(
            loc=brent_shock_pct,
            scale=max(0.01, abs(brent_shock_pct) * 0.30),
            size=n_iter,
        )

        for _, row in agg.iterrows():
            canal = row["canal"]
            base_elast = elasticities.get(canal, -1.0)
            elast_samples = rng.normal(loc=base_elast, scale=0.15, size=n_iter)

            marges_sim  = []
            volumes_sim = []
            profits_sim = []

            for i in range(n_iter):
                delta_cogs  = row["cout_huile_base_moy"] * brent_samples[i]
                cogs_new    = row["cogs_baseline"] + delta_cogs
                nsp_new     = row["nsp_baseline"] * (1.0 + pi_pct)
                vol_new     = compute_volume_impact(row["volume_baseline"], pi_pct, elast_samples[i])

                marge_new   = (nsp_new - cogs_new) / nsp_new if nsp_new > 0 else 0.0
                profit_new  = (nsp_new - cogs_new) * vol_new

                marges_sim.append(marge_new)
                volumes_sim.append(vol_new)
                profits_sim.append(profit_new)

            records.append({
                "scenario":        scenario_key,
                "scenario_label":  params["label"],
                "canal":           canal,
                "marge_p5":        round(float(np.percentile(marges_sim,  5)), 4),
                "marge_p50":       round(float(np.percentile(marges_sim, 50)), 4),
                "marge_p95":       round(float(np.percentile(marges_sim, 95)), 4),
                "volume_p50":      int(np.percentile(volumes_sim, 50)),
                "delta_volume_p5": round(float(np.percentile(volumes_sim,  5) / row["volume_baseline"] - 1), 4),
                "delta_volume_p95":round(float(np.percentile(volumes_sim, 95) / row["volume_baseline"] - 1), 4),
                "profit_p5":       round(float(np.percentile(profits_sim,  5)), 0),
                "profit_p50":      round(float(np.percentile(profits_sim, 50)), 0),
                "profit_p95":      round(float(np.percentile(profits_sim, 95)), 0),
            })

    result = pd.DataFrame(records)
    logger.info(
        "Monte Carlo terminé — {} itérations × {} scénarios × {} canaux",
        n_iter, len(SCENARIOS), agg.shape[0]
    )
    return result


def export_scenario_outputs(
    df: pd.DataFrame,
    elasticities: dict[str, float],
    output_dir: str,
    brent_shock_pct: float = 0.10,
    n_mc_iter: int = 500,
) -> None:
    """Calcule et exporte tous les résultats scénarios en parquet.

    Args:
        df: DataFrame des transactions.
        elasticities: Dict {canal: elasticite}.
        output_dir: Dossier cible.
        brent_shock_pct: Amplitude du choc Brent.
        n_mc_iter: Nombre d'itérations Monte Carlo.
    """
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    run_all_scenarios(df, elasticities, brent_shock_pct).to_parquet(
        out / "scenario_results.parquet", index=False
    )
    run_monte_carlo(df, elasticities, brent_shock_pct, n_mc_iter).to_parquet(
        out / "scenario_monte_carlo.parquet", index=False
    )
    logger.success("Exports scénarios → {}", out)
