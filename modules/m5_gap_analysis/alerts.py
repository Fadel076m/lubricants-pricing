"""Alerts — M5 Gap Analysis.

Classifie les gaps et génère le résumé des alertes par dimension.
Seuils :
    > +5%  → FAVORABLE  (vert)
    -5%..+5% → DANS CIBLE (bleu)
    < -5%  → DÉFAVORABLE (orange)
    < -10% → CRITIQUE    (rouge)
"""

from __future__ import annotations

import pandas as pd
from loguru import logger

from .gap_engine import (
    STATUS_FAVORABLE,
    STATUS_IN_TARGET,
    STATUS_DEFAV,
    STATUS_CRITIQUE,
)

# Codes couleur pour export rapport
COLOR_MAP = {
    STATUS_FAVORABLE: "#27AE60",   # vert
    STATUS_IN_TARGET: "#2980B9",   # bleu
    STATUS_DEFAV:     "#E07B39",   # orange
    STATUS_CRITIQUE:  "#C0392B",   # rouge
}


def compute_alert_summary(gap_global_df: pd.DataFrame) -> dict:
    """Résumé des alertes à partir du gap global.

    Retourne un dict avec les counts et % par statut.
    """
    if gap_global_df.empty:
        return {}

    total = len(gap_global_df)
    counts = gap_global_df["statut_gap"].value_counts().to_dict()

    summary = {
        "total_cibles":    total,
        "n_critique":      counts.get(STATUS_CRITIQUE,  0),
        "n_defavorable":   counts.get(STATUS_DEFAV,     0),
        "n_dans_cible":    counts.get(STATUS_IN_TARGET, 0),
        "n_favorable":     counts.get(STATUS_FAVORABLE, 0),
        "pct_critique":    counts.get(STATUS_CRITIQUE,  0) / total * 100,
        "pct_defavorable": counts.get(STATUS_DEFAV,     0) / total * 100,
        "pct_dans_cible":  counts.get(STATUS_IN_TARGET, 0) / total * 100,
        "pct_favorable":   counts.get(STATUS_FAVORABLE, 0) / total * 100,
    }

    crit = gap_global_df[gap_global_df["statut_gap"] == STATUS_CRITIQUE]
    summary["cibles_critiques"] = crit["target"].tolist() if not crit.empty else []

    return summary


def get_canal_alerts(gap_canal_df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les alertes par canal (pire statut observé sur la période)."""
    if gap_canal_df.empty:
        return pd.DataFrame()

    _STATUS_ORDER = {
        STATUS_CRITIQUE: 0,
        STATUS_DEFAV:    1,
        STATUS_IN_TARGET: 2,
        STATUS_FAVORABLE: 3,
    }

    def _worst_status(series):
        return series.map(_STATUS_ORDER).pipe(lambda s: series.loc[s.idxmin()])

    agg = (
        gap_canal_df
        .groupby(["canal", "target"])
        .agg(
            gap_rel_moy     =("gap_rel",    "mean"),
            gap_abs_total   =("gap_abs",    "sum"),
            statut_dominant =("statut_gap", _worst_status),
            n_mois          =("date",       "count"),
        )
        .reset_index()
        .sort_values("gap_rel_moy")
    )
    agg["couleur"] = agg["statut_dominant"].map(COLOR_MAP)
    return agg


def get_region_alerts(gap_region_df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les alertes par région géographique."""
    if gap_region_df.empty:
        return pd.DataFrame()

    _STATUS_ORDER2 = {
        STATUS_CRITIQUE: 0, STATUS_DEFAV: 1,
        STATUS_IN_TARGET: 2, STATUS_FAVORABLE: 3,
    }

    def _worst_status(series):
        return series.map(_STATUS_ORDER2).pipe(lambda s: series.loc[s.idxmin()])

    agg = (
        gap_region_df
        .groupby(["region", "target"])
        .agg(
            gap_rel_moy     =("gap_rel",    "mean"),
            gap_abs_total   =("gap_abs",    "sum"),
            statut_dominant =("statut_gap", _worst_status),
            n_mois          =("date",       "count"),
        )
        .reset_index()
        .sort_values("gap_rel_moy")
    )
    agg["couleur"] = agg["statut_dominant"].map(COLOR_MAP)
    return agg


def log_alert_summary(summary: dict) -> None:
    """Log les alertes M5 dans le terminal."""
    logger.info("─" * 50)
    logger.info("RÉSUMÉ ALERTES GAP ANALYSIS")
    logger.info("─" * 50)
    logger.info(
        "  CRITIQUE : {}  |  DÉFAVORABLE : {}  |  DANS CIBLE : {}  |  FAVORABLE : {}",
        summary.get("n_critique", 0),
        summary.get("n_defavorable", 0),
        summary.get("n_dans_cible", 0),
        summary.get("n_favorable", 0),
    )
    critiques = summary.get("cibles_critiques", [])
    if critiques:
        logger.warning("  Cibles en CRITIQUE : {}", ", ".join(critiques))
    logger.info("─" * 50)
