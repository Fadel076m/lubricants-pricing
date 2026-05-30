"""Dépendances partagées entre tous les routers."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from fastapi import Query

from modules.m6_dashboard.data_loader import load_all
from modules.shared.filters_core import apply_filters

_VALID_PERIODS = ("all", "2024", "2023", "2022", "6m", "3m", "1m")

# ── Paramètres de filtre communs ──────────────────────────────────────────────

class FilterParams:
    def __init__(
        self,
        period: Literal["all", "2024", "2023", "2022", "6m", "3m", "1m"] = Query(
            "all", description="Période : all, 2024, 2023, 2022, 6m, 3m, 1m"
        ),
        region:  str = Query("ALL", description="Région géographique (ALL = toutes)", max_length=60),
        canal:   str = Query("ALL", description="Canal de vente (ALL = tous)",         max_length=60),
        famille: str = Query("ALL", description="Famille de produits (ALL = toutes)",  max_length=60),
    ):
        self.period  = period
        self.region  = region
        self.canal   = canal
        self.famille = famille


def get_data() -> dict:
    """Retourne le dict complet des datasets (LRU-cached)."""
    return load_all()


def get_filtered_raw(params: FilterParams) -> pd.DataFrame | None:
    """Retourne les transactions brutes filtrées selon les paramètres."""
    data = load_all()
    raw  = data.get("raw")
    if raw is None:
        return None
    return apply_filters(raw, params.region, params.canal, params.famille, params.period)


_PERIOD_LABELS = {
    "all":  "Toute la période (2022–2024)",
    "2024": "Année 2024",
    "2023": "Année 2023",
    "2022": "Année 2022",
    "6m":   "6 derniers mois",
    "3m":   "3 derniers mois",
    "1m":   "Dernier mois (déc. 2024)",
}


def period_label(period: str) -> str:
    return _PERIOD_LABELS.get(period, period)
