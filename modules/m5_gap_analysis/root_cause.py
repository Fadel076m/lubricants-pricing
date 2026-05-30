"""Root Cause Analyzer — M5 Gap Analysis.

Identifie les causes probables des écarts de performance à partir
des données contextuelles (brent, taux change, saisonnalité, canal).
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from loguru import logger

# Seuils de détection de choc externe
BRENT_SHOCK_THRESHOLD  = 0.08   # >8% variation mensuelle = choc brent
FOREX_SHOCK_THRESHOLD  = 0.05   # >5% variation = choc devises
SEASONAL_Q1_MONTHS     = [1, 2, 3]
SEASONAL_Q3_MONTHS     = [7, 8, 9]


# ── Analyse des facteurs macro ────────────────────────────────────────────────

def detect_macro_shocks(df_monthly: pd.DataFrame) -> pd.DataFrame:
    """Détecte les chocs macros mois par mois.

    Colonnes attendues : date, prix_brent_usd, taux_usd_local, inflation_locale
    Retourne : date | brent_variation_pct | forex_variation_pct | choc_brent | choc_forex
    """
    df = df_monthly[["date", "prix_brent_usd", "taux_usd_local", "inflation_locale"]].copy()
    df = df.sort_values("date").reset_index(drop=True)

    df["brent_variation_pct"] = df["prix_brent_usd"].pct_change()
    df["forex_variation_pct"] = df["taux_usd_local"].pct_change()
    df["choc_brent"] = df["brent_variation_pct"].abs() > BRENT_SHOCK_THRESHOLD
    df["choc_forex"]  = df["forex_variation_pct"].abs() > FOREX_SHOCK_THRESHOLD
    df["inflation_haute"] = df["inflation_locale"] > df["inflation_locale"].quantile(0.75)

    return df


def _build_monthly_macro(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Agrège les variables macro en mensuel depuis les données brutes."""
    df = df_raw.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df.groupby("month").agg(
        prix_brent_usd  =("prix_brent_usd",   "mean"),
        taux_usd_local  =("taux_usd_local",   "mean"),
        inflation_locale=("inflation_locale",  "mean"),
    ).reset_index().rename(columns={"month": "date"})


# ── Analyse des causes par dimension ─────────────────────────────────────────

def analyze_sku_root_causes(
    gap_sku_df: pd.DataFrame,
    df_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Enrichit le gap SKU avec les causes probables.

    Logique :
        - Gap négatif volume + choc brent → COGS en hausse, pression marge
        - Gap concentré sur un canal → problème distribution
        - Gap sur un seul SKU famille synth → anomalie produit
    """
    if gap_sku_df.empty:
        return gap_sku_df

    df_macro = _build_monthly_macro(df_raw)
    shocks   = detect_macro_shocks(df_macro)

    # Jointure sur date (mois)
    merged = gap_sku_df.merge(
        shocks[["date", "choc_brent", "choc_forex", "brent_variation_pct"]],
        on="date", how="left"
    )

    def _cause(row) -> str:
        causes = []
        if row["gap_rel"] < -0.10:
            causes.append("Sous-performance critique")
        if row.get("choc_brent") is True:
            causes.append(f"Choc brent ({row['brent_variation_pct']:+.1%})")
        if row.get("choc_forex") is True:
            causes.append("Choc devises")
        if not causes:
            causes.append("Variation demande normale")
        return " | ".join(causes)

    merged["cause_probable"] = merged.apply(_cause, axis=1)
    return merged


def analyze_canal_root_causes(
    gap_canal_df: pd.DataFrame,
    df_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Identifie les canaux sous-performants et propose des causes."""
    if gap_canal_df.empty:
        return gap_canal_df

    df_macro = _build_monthly_macro(df_raw)
    shocks   = detect_macro_shocks(df_macro)

    merged = gap_canal_df.merge(
        shocks[["date", "choc_brent", "choc_forex", "brent_variation_pct"]],
        on="date", how="left"
    )

    # Canaux sensibles au brent (logistique lourde)
    CANAL_BRENT_SENSIBLE = {"B2B OEM", "B2B Industrie"}

    def _cause(row) -> str:
        causes = []
        if row["gap_rel"] < -0.10:
            causes.append("Perte de volume majeure sur canal")
        if row.get("choc_brent") and row.get("canal") in CANAL_BRENT_SENSIBLE:
            causes.append("Répercussion hausse brent (OEM/Industrie)")
        if row.get("choc_forex"):
            causes.append("Pression marge importation")
        if not causes:
            causes.append("Fluctuation saisonnière / mix produit")
        return " | ".join(causes)

    if "canal" in merged.columns:
        merged["cause_probable"] = merged.apply(_cause, axis=1)
    return merged


# ── Résumé des causes et recommandations ─────────────────────────────────────

def generate_recommendations(gap_global_df: pd.DataFrame) -> list[str]:
    """Génère une liste de recommandations textuelles à partir du gap global."""
    recs = []
    if gap_global_df.empty:
        return ["Aucune donnée de gap disponible."]

    for _, row in gap_global_df.iterrows():
        target  = row["target"]
        status  = row["statut_gap"]
        gap_pct = row["gap_rel"] * 100 if pd.notna(row["gap_rel"]) else 0

        if target == "volume_vendu":
            if status == "CRITIQUE":
                recs.append(
                    f"URGENT — Volume en retard de {gap_pct:.1f}% vs forecast. "
                    "Revoir la stratégie promotionnelle et la pénétration canal."
                )
            elif status == "DÉFAVORABLE":
                recs.append(
                    f"Volume sous forecast ({gap_pct:.1f}%). "
                    "Analyser le mix canal B2B / Retail et les remises accordées."
                )
            elif status == "FAVORABLE":
                recs.append(
                    f"Volume au-dessus du forecast (+{gap_pct:.1f}%). "
                    "Vérifier la capacité d'approvisionnement pour maintenir la dynamique."
                )

        elif target == "nsp":
            if status in ("CRITIQUE", "DÉFAVORABLE"):
                recs.append(
                    f"NSP moyen sous cible ({gap_pct:.1f}%). "
                    "Revoir la politique de remises — risque érosion marge brute."
                )
            elif status == "FAVORABLE":
                recs.append(
                    f"NSP supérieur aux prévisions (+{gap_pct:.1f}%). "
                    "Opportunité de consolider les hausses de prix sur les canaux premium."
                )

        elif target == "marge_brute_pct":
            if status == "CRITIQUE":
                recs.append(
                    f"MARGE CRITIQUE — écart de {gap_pct:.1f}% vs forecast. "
                    "Déclencher revue PI d'urgence et analyse COGS (brent / forex)."
                )
            elif status == "DÉFAVORABLE":
                recs.append(
                    f"Marge sous forecast ({gap_pct:.1f}%). "
                    "Monitorer les composantes COGS et envisager un PI sur SKUs à risque."
                )

    if not recs:
        recs.append("Performance dans les cibles — continuer le suivi mensuel.")

    return recs


# ── Top N SKUs sous-performants ───────────────────────────────────────────────

def get_top_critical_skus(gap_sku_df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Retourne les N SKUs avec le plus grand écart défavorable (gap_rel le plus bas)."""
    if gap_sku_df.empty:
        return pd.DataFrame()

    agg = (
        gap_sku_df
        .groupby("sku_code")
        .agg(
            gap_rel_moy =("gap_rel",   "mean"),
            gap_abs_total=("gap_abs",  "sum"),
            statut_dominant=("statut_gap", lambda x: x.value_counts().index[0]),
        )
        .reset_index()
        .sort_values("gap_rel_moy")
        .head(n)
    )
    return agg
