"""Router /api/simulate — Simulateur PI et comparaison de scénarios."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from modules.m7_api.dependencies import get_data
from modules.m7_api.schemas import PISimulateRequest, PIProductResult, ScenariosRequest, ScenarioResult
from modules.shared.filters_core import apply_filters

router = APIRouter(prefix="/simulate", tags=["Simulation"])


@router.post("/pi", response_model=list[PIProductResult], summary="Simulateur de hausse de prix (PI)")
def simulate_pi(body: PISimulateRequest) -> list[PIProductResult]:
    """
    Calcule la hausse de prix (Price Increase) nécessaire pour chaque produit
    afin d'atteindre la marge cible après un choc sur les coûts matière.

    Formule :
    - COGS_new = COGS + cout_huile_base × brent_shock_pct
    - NSP_cible = COGS_new / (1 - target_margin_pct)
    - PI_requis = (NSP_cible / NSP - 1) × 100

    Urgence :
    - URGENT  : PI > 5%
    - MODERE  : PI entre 2% et 5%
    - OK      : PI < 2%
    """
    data = get_data()
    raw  = data.get("raw")
    if raw is None:
        raise HTTPException(status_code=404, detail="Données brutes non disponibles.")

    filtered = apply_filters(raw, body.region, body.canal, body.famille, body.period)
    if filtered is None or filtered.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée pour ces filtres.")

    grp = (
        filtered.groupby("sku_id")
        .agg(
            nsp             =("nsp",             "mean"),
            cogs            =("cogs_total",       "mean"),
            cout_huile_base =("cout_huile_base",  "mean"),
            marge           =("marge_brute_pct",  "mean"),
            canal_top       =("canal", lambda x: x.value_counts().index[0]),
        )
        .reset_index()
        .fillna(0)
    )

    margin_denom = 1 - body.target_margin_pct
    grp["cogs_new"]  = grp["cogs"] + grp["cout_huile_base"] * body.brent_shock_pct
    grp["nsp_cible"] = grp["cogs_new"] / margin_denom if margin_denom != 0 else grp["cogs_new"]
    grp["pi_requis"] = grp.apply(
        lambda r: (r["nsp_cible"] / r["nsp"] - 1) * 100 if r["nsp"] != 0 else 0.0, axis=1
    )

    def _urgence(pi: float) -> str:
        if pi > 5:
            return "URGENT"
        if pi > 2:
            return "MODERE"
        return "OK"

    grp = grp.sort_values("pi_requis", ascending=False)

    return [
        PIProductResult(
            sku_id              = row["sku_id"],
            canal_principal     = row["canal_top"],
            nsp_actuel          = round(float(row["nsp"]), 2),
            cogs_actuel         = round(float(row["cogs"]), 2),
            pi_requis_pct       = round(float(row["pi_requis"]), 2),
            marge_actuelle_pct  = round(float(row["marge"]) * 100, 2),
            urgence             = _urgence(float(row["pi_requis"])),
        )
        for _, row in grp.iterrows()
    ]


@router.post("/scenarios", response_model=list[ScenarioResult], summary="Comparaison de 3 scénarios de prix")
def simulate_scenarios(body: ScenariosRequest) -> list[ScenarioResult]:
    """
    Compare l'impact de 3 stratégies de prix sur le profit, le volume et la marge.

    - Scénario A : +3% de prix
    - Scénario B : +5% de prix (recommandé)
    - Scénario C : prix inchangés

    Hypothèse : élasticité-prix = -0.5 (une hausse de 10% réduit le volume de 5%).
    """
    data = get_data()
    raw  = data.get("raw")
    if raw is None:
        raise HTTPException(status_code=404, detail="Données brutes non disponibles.")

    filtered = apply_filters(raw, body.region, body.canal, body.famille, body.period)
    if filtered is None or filtered.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée pour ces filtres.")

    total_ca   = filtered["ca"].sum()
    total_cogs = (filtered["ca"] * (1 - filtered["marge_brute_pct"])).sum()
    old_profit = total_ca - total_cogs
    old_marge  = (total_ca - total_cogs) / total_ca if total_ca > 0 else 0

    ELASTICITY = -0.5
    _cfg = {
        "A": ("Hausse des prix de 3%",    0.03, False),
        "B": ("Hausse des prix de 5%",    0.05, True),
        "C": ("Prix inchangés",           0.00, False),
    }

    results = []
    for scen_id, (desc, pi, recommande) in _cfg.items():
        vol_factor = 1 + ELASTICITY * pi
        new_ca     = total_ca * (1 + pi) * vol_factor
        new_cogs   = total_cogs * vol_factor
        new_profit = new_ca - new_cogs
        new_marge  = (new_ca - new_cogs) / new_ca if new_ca > 0 else 0

        results.append(ScenarioResult(
            scenario          = scen_id,
            description       = desc,
            delta_profit_pct  = round((new_profit - old_profit) / abs(old_profit) * 100 if old_profit else 0, 2),
            delta_volume_pct  = round((vol_factor - 1) * 100, 2),
            delta_marge_pts   = round((new_marge - old_marge) * 100, 2),
            recommande        = recommande,
        ))

    return results
