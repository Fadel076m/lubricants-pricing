"""Logique de filtrage pure pandas — partagée entre le Dashboard (M6) et l'API (M7).

Sans dépendance Dash pour permettre l'import depuis les deux contextes.
"""

from __future__ import annotations

import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    region: str = "ALL",
    canal: str = "ALL",
    famille: str = "ALL",
    period: str = "all",
) -> pd.DataFrame:
    """Filtre un DataFrame selon les paramètres de la barre de filtres."""
    if region != "ALL":
        df = df[df["region"] == region]
    if canal != "ALL":
        df = df[df["canal"] == canal]
    if famille != "ALL" and "famille" in df.columns:
        df = df[df["famille"] == famille]

    if period != "all" and "date" in df.columns:
        if period == "2024":
            df = df[df["date"].dt.year == 2024]
        elif period == "2023":
            df = df[df["date"].dt.year == 2023]
        elif period == "2022":
            df = df[df["date"].dt.year == 2022]
        elif period in ("1m", "3m", "6m"):
            max_date = df["date"].max()
            months = {"1m": 1, "3m": 3, "6m": 6}[period]
            cutoff = max_date - pd.DateOffset(months=months)
            df = df[df["date"] > cutoff]

    return df
