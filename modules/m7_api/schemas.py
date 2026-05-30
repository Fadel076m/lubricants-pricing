"""Modèles Pydantic v2 — requêtes et réponses de l'API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Réponses KPI ─────────────────────────────────────────────────────────────

class KpiResponse(BaseModel):
    ca: float              = Field(description="Chiffre d'affaires total (XOF)")
    ca_delta_pct: float    = Field(description="Variation CA vs mois précédent (%)")
    volume: float          = Field(description="Volume vendu total (litres)")
    volume_delta_pct: float= Field(description="Variation volume vs mois précédent (%)")
    marge_pct: float       = Field(description="Marge brute moyenne (%)")
    marge_delta_pts: float = Field(description="Variation marge vs mois précédent (pts)")
    nsp: float             = Field(description="Prix net moyen (XOF/L)")
    nsp_delta_pct: float   = Field(description="Variation NSP vs mois précédent (%)")
    periode: str           = Field(description="Libellé de la période analysée")
    dernier_mois: str      = Field(description="Dernier mois disponible dans les données")


# ── Réponses Produits ─────────────────────────────────────────────────────────

class ProductItem(BaseModel):
    sku_id: str
    famille: str | None    = None
    nsp_moyen: float       = Field(description="Prix net moyen (XOF/L)")
    marge_pct: float       = Field(description="Marge brute moyenne (%)")
    volume_total: float    = Field(description="Volume total vendu (litres)")
    ca_total: float        = Field(description="Chiffre d'affaires total (XOF)")
    statut_marge: str      = Field(description="OK / ATTENTION / CRITIQUE selon seuils")


class ProductsResponse(BaseModel):
    nb_produits: int
    produits: list[ProductItem]


# ── Réponses Pricing ──────────────────────────────────────────────────────────

class BenchmarkItem(BaseModel):
    canal: str
    nsp_moyen: float       = Field(description="Notre prix net moyen (XOF/L)")
    prix_concurrent: float = Field(description="Prix concurrent moyen (XOF/L)")
    ecart_pct: float       = Field(description="Écart (NSP - concurrent) / concurrent * 100")


class TrendPoint(BaseModel):
    mois: str
    nsp: float
    cogs: float
    marge_pct: float


# ── Réponses Forecasts ────────────────────────────────────────────────────────

class ForecastItem(BaseModel):
    horizon_days: int
    target: str
    yhat: float
    yhat_lower: float | None = None
    yhat_upper: float | None = None


# ── Réponses Gap ──────────────────────────────────────────────────────────────

class GapSkuItem(BaseModel):
    sku_code: str
    hit_rate_pct: float    = Field(description="% de mois dans la cible (écart ≥ -5%)")
    pire_ecart_pct: float  = Field(description="Pire écart mensuel (%)")
    meilleur_ecart_pct: float = Field(description="Meilleur écart mensuel (%)")
    nb_mois: int           = Field(description="Nombre de mois analysés")
    statut: str            = Field(description="FIABLE / ATTENTION / CRITIQUE")


class GapRegionItem(BaseModel):
    region: str
    gap_rel_moyen: float   = Field(description="Écart moyen réel vs prévu (%)")
    statut: str


# ── Corps de requête Simulation ───────────────────────────────────────────────

class PISimulateRequest(BaseModel):
    brent_shock_pct: float = Field(0.10, ge=0, le=0.50,
                                   description="Choc coûts matière (0.10 = +10%)")
    target_margin_pct: float = Field(0.30, ge=0.10, le=0.60,
                                     description="Marge cible (0.30 = 30%)")
    region: str  = Field("ALL", description="Filtrer par région (ALL = toutes)")
    canal: str   = Field("ALL", description="Filtrer par canal (ALL = tous)")
    famille: str = Field("ALL", description="Filtrer par famille (ALL = toutes)")
    period: str  = Field("all", description="Période : all, 2024, 2023, 6m, 3m, 1m")


class PIProductResult(BaseModel):
    sku_id: str
    canal_principal: str
    nsp_actuel: float
    cogs_actuel: float
    pi_requis_pct: float
    marge_actuelle_pct: float
    urgence: str           = Field(description="URGENT / MODERE / OK")


class ScenariosRequest(BaseModel):
    region: str  = Field("ALL")
    canal: str   = Field("ALL")
    famille: str = Field("ALL")
    period: str  = Field("all")


class ScenarioResult(BaseModel):
    scenario: str          = Field(description="A (+3%) / B (+5%) / C (inchangé)")
    description: str
    delta_profit_pct: float
    delta_volume_pct: float
    delta_marge_pts: float
    recommande: bool
