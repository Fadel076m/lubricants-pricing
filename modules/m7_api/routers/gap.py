"""Router /api/gap — Analyse des écarts réel vs prévision."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from modules.m7_api.dependencies import FilterParams, get_data, get_filtered_raw
from modules.m7_api.schemas import GapSkuItem, GapRegionItem

router = APIRouter(prefix="/gap", tags=["Analyse des Écarts"])


def _statut_fiabilite(hit_rate: float) -> str:
    if hit_rate >= 70:
        return "FIABLE"
    if hit_rate >= 50:
        return "ATTENTION"
    return "CRITIQUE"


def _statut_region(gap_rel: float) -> str:
    if gap_rel >= 0.05:
        return "FAVORABLE"
    if gap_rel >= -0.05:
        return "DANS CIBLE"
    if gap_rel >= -0.10:
        return "DÉFAVORABLE"
    return "CRITIQUE"


def _filter_gap_by_period(gap_df: pd.DataFrame, period: str) -> pd.DataFrame:
    if period == "all" or "date" not in gap_df.columns:
        return gap_df
    gap_df = gap_df.copy()
    gap_df["date"] = pd.to_datetime(gap_df["date"])
    if period in ("2024", "2023", "2022"):
        return gap_df[gap_df["date"].dt.year == int(period)]
    if period in ("1m", "3m", "6m"):
        max_date = gap_df["date"].max()
        months = {"1m": 1, "3m": 3, "6m": 6}[period]
        return gap_df[gap_df["date"] > max_date - pd.DateOffset(months=months)]
    return gap_df


@router.get("/sku", response_model=list[GapSkuItem], summary="Fiabilité des prévisions par produit")
def get_gap_sku(params: FilterParams = Depends()) -> list[GapSkuItem]:
    """
    Pour chaque produit (SKU), retourne le % de mois où l'objectif de vente
    a été atteint (écart réel vs prévu ≥ -5%).
    - FIABLE    : ≥ 70% des mois dans la cible
    - ATTENTION : 50–70%
    - CRITIQUE  : < 50% (manque la cible un mois sur deux)
    """
    data    = get_data()
    gap_sku = data.get("gap_sku")
    if gap_sku is None or gap_sku.empty:
        raise HTTPException(status_code=404, detail="gap_sku.parquet absent — lancer run_m5.py")

    filtered_raw = get_filtered_raw(params)
    df = gap_sku[gap_sku["target"] == "volume_vendu"] if "target" in gap_sku.columns else gap_sku
    df = _filter_gap_by_period(df, params.period)

    if filtered_raw is not None and not filtered_raw.empty:
        sku_ids = filtered_raw["sku_id"].unique()
        df = df[df["sku_code"].isin(sku_ids)]

    if df.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée de gap pour ces filtres.")

    agg = (
        df.groupby("sku_code")
        .apply(lambda g: pd.Series({
            "hit_rate":       (g["gap_rel"] >= -0.05).mean() * 100,
            "pire_ecart":     g["gap_rel"].min() * 100,
            "meilleur_ecart": g["gap_rel"].max() * 100,
            "nb_mois":        len(g),
        }))
        .reset_index()
        .fillna(0)
        .sort_values("hit_rate")
    )

    return [
        GapSkuItem(
            sku_code             = row["sku_code"],
            hit_rate_pct         = round(float(row["hit_rate"]), 1),
            pire_ecart_pct       = round(float(row["pire_ecart"]), 1),
            meilleur_ecart_pct   = round(float(row["meilleur_ecart"]), 1),
            nb_mois              = int(row["nb_mois"]),
            statut               = _statut_fiabilite(float(row["hit_rate"])),
        )
        for _, row in agg.iterrows()
    ]


@router.get("/region", response_model=list[GapRegionItem], summary="Écarts par région")
def get_gap_region(params: FilterParams = Depends()) -> list[GapRegionItem]:
    """
    Retourne l'écart moyen réel vs prévu pour chaque région.
    Un écart positif = on dépasse les prévisions dans cette région.
    """
    data       = get_data()
    gap_region = data.get("gap_region")
    if gap_region is None or gap_region.empty:
        raise HTTPException(status_code=404, detail="gap_region.parquet absent — lancer run_m5.py")

    df = _filter_gap_by_period(gap_region, params.period)

    col_region = "region" if "region" in df.columns else df.columns[0]
    agg = df.groupby(col_region)["gap_rel"].mean().reset_index().fillna(0)

    return [
        GapRegionItem(
            region        = row[col_region],
            gap_rel_moyen = round(float(row["gap_rel"]) * 100, 2),
            statut        = _statut_region(float(row["gap_rel"])),
        )
        for _, row in agg.sort_values("gap_rel").iterrows()
    ]
