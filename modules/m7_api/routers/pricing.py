"""Router /api/pricing — Benchmark prix et tendances NSP/COGS."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from modules.m7_api.dependencies import FilterParams, get_filtered_raw
from modules.m7_api.schemas import BenchmarkItem, TrendPoint

router = APIRouter(prefix="/pricing", tags=["Analyse des Prix"])


@router.get(
    "/benchmark",
    response_model=list[BenchmarkItem],
    summary="Notre prix vs concurrent par canal de vente",
)
def get_benchmark(params: FilterParams = Depends()) -> list[BenchmarkItem]:
    """
    Retourne la comparaison NSP moyen vs prix concurrent pour chaque canal.
    Un écart négatif signifie qu'on est moins cher que le concurrent.
    """
    filtered = get_filtered_raw(params)
    if filtered is None or filtered.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée pour ces filtres.")

    by_canal = (
        filtered.groupby("canal")
        .agg(nsp=("nsp", "mean"), concurrent=("prix_concurrent", "mean"))
        .reset_index()
        .fillna(0)
    )

    return [
        BenchmarkItem(
            canal           = row["canal"],
            nsp_moyen       = round(float(row["nsp"]), 2),
            prix_concurrent = round(float(row["concurrent"]), 2),
            ecart_pct       = round((float(row["nsp"]) - float(row["concurrent"])) / float(row["concurrent"]) * 100, 2)
                              if float(row["concurrent"]) != 0 else 0.0,
        )
        for _, row in by_canal.iterrows()
    ]


@router.get(
    "/trend",
    response_model=list[TrendPoint],
    summary="Évolution mensuelle NSP et COGS",
)
def get_trend(params: FilterParams = Depends()) -> list[TrendPoint]:
    """
    Retourne la tendance mensuelle du prix de vente (NSP) et du coût de revient (COGS).
    La différence NSP - COGS représente la marge unitaire.
    """
    filtered = get_filtered_raw(params)
    if filtered is None or filtered.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée pour ces filtres.")

    monthly = (
        filtered.groupby("month")
        .agg(nsp=("nsp", "mean"), cogs=("cogs_total", "mean"),
             marge=("marge_brute_pct", "mean"))
        .reset_index()
        .fillna(0)
        .sort_values("month")
    )

    return [
        TrendPoint(
            mois      = row["month"].strftime("%Y-%m"),
            nsp       = round(row["nsp"], 2),
            cogs      = round(row["cogs"], 2),
            marge_pct = round(row["marge"] * 100, 2),
        )
        for _, row in monthly.iterrows()
    ]
