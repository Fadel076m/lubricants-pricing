"""Router /api/products — Catalogue produits et marges."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated

from modules.m7_api.dependencies import FilterParams, get_filtered_raw
from modules.m7_api.schemas import ProductItem, ProductsResponse

router = APIRouter(prefix="/products", tags=["Produits"])

_SORT_COLS = {"marge": "marge_pct", "volume": "volume_total", "ca": "ca_total", "nsp": "nsp_moyen"}


def _statut(marge: float) -> str:
    if marge < 20:
        return "CRITIQUE"
    if marge < 30:
        return "ATTENTION"
    return "OK"


@router.get("", response_model=ProductsResponse, summary="Liste des produits avec marges")
def list_products(
    params: FilterParams = Depends(),
    sort_by: Annotated[str, Query(description="Trier par : marge, volume, ca, nsp")] = "marge",
    limit: Annotated[int, Query(ge=1, le=100, description="Nombre max de produits")] = 50,
    ordre: Annotated[str, Query(description="asc ou desc")] = "asc",
) -> ProductsResponse:
    """
    Retourne la liste des produits agrégés avec marge brute, volume, CA et NSP moyens.
    Filtrable par période, région, canal, famille.
    """
    filtered = get_filtered_raw(params)
    if filtered is None or filtered.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée pour ces filtres.")

    agg = (
        filtered.groupby(["sku_id", "famille"])
        .agg(
            nsp_moyen    =("nsp",             "mean"),
            marge_pct    =("marge_brute_pct", "mean"),
            volume_total =("volume_vendu",    "sum"),
            ca_total     =("ca",              "sum"),
        )
        .reset_index()
    )
    agg["marge_pct"]  = agg["marge_pct"] * 100
    agg["nsp_moyen"]  = agg["nsp_moyen"].round(2)
    agg["ca_total"]   = agg["ca_total"].round(2)
    agg["statut_marge"] = agg["marge_pct"].apply(_statut)

    sort_col = _SORT_COLS.get(sort_by, "marge_pct")
    agg = agg.sort_values(sort_col, ascending=(ordre == "asc")).head(limit)

    produits = [
        ProductItem(
            sku_id        = row["sku_id"],
            famille       = row.get("famille"),
            nsp_moyen     = round(row["nsp_moyen"], 2),
            marge_pct     = round(row["marge_pct"], 2),
            volume_total  = round(row["volume_total"], 0),
            ca_total      = round(row["ca_total"], 2),
            statut_marge  = row["statut_marge"],
        )
        for _, row in agg.iterrows()
    ]

    return ProductsResponse(nb_produits=len(produits), produits=produits)


@router.get("/{sku_id}", response_model=ProductItem, summary="Détail d'un produit")
def get_product(sku_id: str, params: FilterParams = Depends()) -> ProductItem:
    """Retourne les métriques agrégées d'un seul produit (SKU)."""
    filtered = get_filtered_raw(params)
    if filtered is None or filtered.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée pour ces filtres.")

    sku_df = filtered[filtered["sku_id"] == sku_id]
    if sku_df.empty:
        raise HTTPException(status_code=404, detail=f"Produit '{sku_id}' introuvable.")

    marge_pct = sku_df["marge_brute_pct"].mean() * 100
    return ProductItem(
        sku_id       = sku_id,
        famille      = sku_df["famille"].iloc[0] if "famille" in sku_df.columns else None,
        nsp_moyen    = round(sku_df["nsp"].mean(), 2),
        marge_pct    = round(marge_pct, 2),
        volume_total = round(sku_df["volume_vendu"].sum(), 0),
        ca_total     = round(sku_df["ca"].sum(), 2),
        statut_marge = _statut(marge_pct),
    )
