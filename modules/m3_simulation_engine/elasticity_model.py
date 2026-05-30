"""Elasticity model wrapper — M3 Pricing Simulation Engine.

Pourquoi ce fichier ?
    Un PI sans prise en compte de l'élasticité-prix est incomplet :
    un PI de +5% sur le canal B2C GMS (élasticité −1.4) fait perdre
    plus de volume que sur B2B OEM (élasticité −0.3, contrats long terme).
    Ce fichier encapsule le modèle OLS log-log de M1 et l'applique
    au calcul d'impact volume et revenu après un PI.

Formule :
    %ΔVolume = élasticité × %ΔPrix
    Volume_new = Volume_base × (1 + PI)^élasticité
"""

import numpy as np
import pandas as pd
from loguru import logger

from modules.m1_market_insights.analysis import compute_price_elasticity


def fit_elasticities(df: pd.DataFrame) -> dict[str, float]:
    """Calibre les élasticités-prix par canal sur les données historiques.

    Wrapper autour du modèle OLS log-log de M1.

    Args:
        df: DataFrame des transactions brutes.

    Returns:
        Dict {canal: elasticite} trié du plus élastique au moins élastique.
    """
    elast_df = compute_price_elasticity(df)
    result = dict(zip(elast_df["canal"], elast_df["elasticite"]))
    logger.info("Élasticités calibrées : {}", result)
    return result


def compute_volume_impact(
    base_volume: float,
    pi_pct: float,
    elasticity: float,
) -> float:
    """Volume après PI selon le modèle log-log.

    Formule : Volume_new = Volume_base × (1 + PI_pct)^élasticité

    Args:
        base_volume: Volume de référence (litres/mois).
        pi_pct: Price increase appliqué (ex: 0.05 pour +5%).
        elasticity: Coefficient d'élasticité (négatif → demande baisse).

    Returns:
        Nouveau volume estimé.
    """
    return round(base_volume * ((1.0 + pi_pct) ** elasticity), 2)


def compute_revenue_impact_by_canal(
    df: pd.DataFrame,
    pi_pct: float,
    elasticities: dict[str, float],
) -> pd.DataFrame:
    """Impact revenu d'un PI par canal.

    Pour chaque canal : calcule le nouveau NSP, le nouveau volume,
    le nouveau CA et la variation vs baseline.

    Args:
        df: DataFrame des transactions brutes.
        pi_pct: Price increase à appliquer.
        elasticities: Dict {canal: elasticite}.

    Returns:
        DataFrame colonnes :
            canal | nsp_baseline | nsp_new | volume_baseline |
            volume_new | ca_baseline | ca_new |
            delta_volume_pct | delta_ca_pct | elasticite
    """
    agg = (
        df.groupby("canal")
        .agg(
            nsp_baseline   =("nsp",          "mean"),
            volume_baseline=("volume_vendu", "sum"),
        )
        .reset_index()
    )

    rows = []
    for _, row in agg.iterrows():
        canal = row["canal"]
        elast = elasticities.get(canal, -1.0)

        nsp_new    = row["nsp_baseline"] * (1.0 + pi_pct)
        vol_new    = compute_volume_impact(row["volume_baseline"], pi_pct, elast)
        ca_base    = row["nsp_baseline"] * row["volume_baseline"]
        ca_new     = nsp_new * vol_new

        rows.append({
            "canal":             canal,
            "nsp_baseline":      round(row["nsp_baseline"], 2),
            "nsp_new":           round(nsp_new, 2),
            "volume_baseline":   int(row["volume_baseline"]),
            "volume_new":        int(vol_new),
            "ca_baseline":       round(ca_base, 0),
            "ca_new":            round(ca_new, 0),
            "delta_volume_pct":  round((vol_new - row["volume_baseline"]) / row["volume_baseline"], 4),
            "delta_ca_pct":      round((ca_new - ca_base) / ca_base, 4),
            "elasticite":        round(elast, 2),
        })

    result = pd.DataFrame(rows).sort_values("delta_ca_pct")
    logger.info("Impact CA par canal pour PI {:+.0%} calculé", pi_pct)
    return result
