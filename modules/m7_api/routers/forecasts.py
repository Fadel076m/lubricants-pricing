"""Router /api/forecasts — Prévisions 30/60/90 jours."""

from __future__ import annotations

import math
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from modules.m7_api.dependencies import get_data
from modules.m7_api.schemas import ForecastItem

router = APIRouter(prefix="/forecasts", tags=["Prévisions"])

_VALID_TARGETS  = {"volume_vendu", "nsp", "marge_brute_pct"}
_VALID_HORIZONS = {30, 60, 90}


@router.get("", response_model=list[ForecastItem], summary="Prévisions 30/60/90 jours")
def get_forecasts(
    target: Annotated[
        str,
        Query(description="Variable à prévoir : volume_vendu, nsp, marge_brute_pct"),
    ] = "volume_vendu",
    horizon: Annotated[
        int | None,
        Query(description="Horizon en jours : 30, 60 ou 90. Omettez pour les 3 horizons."),
    ] = None,
) -> list[ForecastItem]:
    """
    Retourne les prévisions ML (Prophet / LSTM / XGBoost) pour la variable cible.
    - volume_vendu : modèle LSTM (MAPE 2.68%)
    - nsp          : modèle Prophet (MAPE 3.99%)
    - marge_brute_pct : modèle XGBoost (MAPE 1.49%)
    """
    if target not in _VALID_TARGETS:
        raise HTTPException(
            status_code=422,
            detail=f"target invalide. Valeurs acceptées : {sorted(_VALID_TARGETS)}",
        )
    if horizon is not None and horizon not in _VALID_HORIZONS:
        raise HTTPException(
            status_code=422,
            detail=f"horizon invalide. Valeurs acceptées : {sorted(_VALID_HORIZONS)}",
        )

    data = get_data()
    forecasts = data.get("forecasts")
    if forecasts is None or forecasts.empty:
        raise HTTPException(
            status_code=404,
            detail="Prévisions non disponibles — lancer d'abord run_m4.py",
        )

    df = forecasts[forecasts["target"] == target]
    if horizon is not None:
        df = df[df["horizon_days"] == horizon]

    if df.empty:
        raise HTTPException(status_code=404, detail="Aucune prévision pour ces paramètres.")

    def _opt_float(row: pd.Series, col: str) -> float | None:
        if col not in row:
            return None
        v = row[col]
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return round(float(v), 4)

    results = []
    for _, row in df.sort_values("horizon_days").iterrows():
        results.append(ForecastItem(
            horizon_days = int(row["horizon_days"]),
            target       = row["target"],
            yhat         = round(float(row["yhat"]), 4),
            yhat_lower   = _opt_float(row, "yhat_lower"),
            yhat_upper   = _opt_float(row, "yhat_upper"),
        ))
    return results
