"""Router /api/kpis — Indicateurs clés de performance."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from modules.m7_api.dependencies import FilterParams, get_filtered_raw, period_label
from modules.m7_api.schemas import KpiResponse
from modules.m6_dashboard.data_loader import get_kpi_global

router = APIRouter(prefix="/kpis", tags=["KPIs"])


@router.get("", response_model=KpiResponse, summary="Indicateurs clés de performance")
def get_kpis(params: FilterParams = Depends()) -> KpiResponse:
    """
    Retourne les 4 KPIs principaux (CA, Volume, Marge, NSP) pour la période
    et les filtres sélectionnés, avec la variation vs le mois précédent.
    """
    filtered = get_filtered_raw(params)
    if filtered is None or filtered.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée pour ces filtres.")

    kpis = get_kpi_global(filtered)
    if not kpis:
        raise HTTPException(status_code=404, detail="Impossible de calculer les KPIs.")

    return KpiResponse(
        ca               = round(kpis["ca"], 2),
        ca_delta_pct     = round(kpis["ca_delta"], 2),
        volume           = round(kpis["volume"], 0),
        volume_delta_pct = round(kpis["volume_delta"], 2),
        marge_pct        = round(kpis["marge"], 2),
        marge_delta_pts  = round(kpis["marge_delta"], 2),
        nsp              = round(kpis["nsp"], 2),
        nsp_delta_pct    = round(kpis["nsp_delta"], 2),
        periode          = period_label(params.period),
        dernier_mois     = kpis["month_label"],
    )
