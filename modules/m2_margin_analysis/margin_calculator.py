"""Margin aggregation calculator — M2 Margin Analysis.

Pourquoi ce fichier ?
    Le COGS explique les coûts ; ce fichier calcule la marge résultante
    selon toutes les dimensions utiles à un Pricing Manager : SKU, canal,
    région, famille, et leurs croisements. C'est la base de tout arbitrage
    de portefeuille (quels SKUs sacrifier, quels canaux défendre).
"""

import pandas as pd
from loguru import logger


# ── Par SKU ───────────────────────────────────────────────────────────────────
def compute_margin_by_sku(df: pd.DataFrame) -> pd.DataFrame:
    """Marge brute moyenne par SKU sur toute la période.

    Returns:
        DataFrame trié par marge croissante, colonnes :
            sku_id | produit | famille | marge_brute_pct_moy |
            marge_brute_moy | nsp_moy | cogs_moy | volume_total
    """
    result = (
        df.groupby(["sku_id", "produit", "famille"])
        .agg(
            marge_brute_pct_moy=("marge_brute_pct", "mean"),
            marge_brute_moy    =("marge_brute",     "mean"),
            nsp_moy            =("nsp",              "mean"),
            cogs_moy           =("cogs_total",       "mean"),
            volume_total       =("volume_vendu",     "sum"),
        )
        .reset_index()
        .sort_values("marge_brute_pct_moy")
        .round(4)
    )
    logger.info("Marge par SKU : {} SKUs analysés", len(result))
    return result


# ── Par canal ─────────────────────────────────────────────────────────────────
def compute_margin_by_channel(df: pd.DataFrame) -> pd.DataFrame:
    """Marge brute par canal avec volume pondéré et contribution au CA.

    Returns:
        DataFrame trié par marge croissante, colonnes :
            canal | marge_brute_pct_moy | marge_brute_pct_med |
            nsp_moy | volume_total | ca_total | contribution_ca_pct
    """
    agg = (
        df.groupby("canal")
        .agg(
            marge_brute_pct_moy=("marge_brute_pct", "mean"),
            marge_brute_pct_med=("marge_brute_pct", "median"),
            nsp_moy            =("nsp",              "mean"),
            volume_total       =("volume_vendu",     "sum"),
            ca_total           =("nsp",              lambda s: (s * df.loc[s.index, "volume_vendu"]).sum()),
        )
        .reset_index()
    )

    agg["contribution_ca_pct"] = (agg["ca_total"] / agg["ca_total"].sum()).round(4)
    agg = agg.sort_values("marge_brute_pct_moy").round(4)

    logger.info("Marge par canal : {} canaux analysés", len(agg))
    return agg


# ── Par région ────────────────────────────────────────────────────────────────
def compute_margin_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Marge brute par région avec exposition FX.

    Inclut le taux USD/local moyen pour contextualiser l'impact devise.

    Returns:
        DataFrame colonnes :
            region | devise_locale | marge_brute_pct_moy |
            nsp_moy | cogs_moy | taux_usd_local_moy | volume_total
    """
    result = (
        df.groupby(["region", "devise_locale"])
        .agg(
            marge_brute_pct_moy=("marge_brute_pct", "mean"),
            nsp_moy            =("nsp",              "mean"),
            cogs_moy           =("cogs_total",       "mean"),
            taux_usd_local_moy =("taux_usd_local",   "mean"),
            volume_total       =("volume_vendu",     "sum"),
        )
        .reset_index()
        .sort_values("marge_brute_pct_moy")
        .round(4)
    )
    logger.info("Marge par région : {} régions analysées", len(result))
    return result


# ── Par famille ───────────────────────────────────────────────────────────────
def compute_margin_by_family(df: pd.DataFrame) -> pd.DataFrame:
    """Marge brute par famille de produit.

    Returns:
        DataFrame colonnes :
            famille | marge_brute_pct_moy | marge_brute_pct_min |
            marge_brute_pct_max | n_skus | volume_total
    """
    result = (
        df.groupby("famille")
        .agg(
            marge_brute_pct_moy=("marge_brute_pct", "mean"),
            marge_brute_pct_min=("marge_brute_pct", "min"),
            marge_brute_pct_max=("marge_brute_pct", "max"),
            n_skus             =("sku_id",           "nunique"),
            volume_total       =("volume_vendu",     "sum"),
        )
        .reset_index()
        .sort_values("marge_brute_pct_moy")
        .round(4)
    )
    logger.info("Marge par famille : {} familles analysées", len(result))
    return result


# ── Croisement SKU × Canal ────────────────────────────────────────────────────
def compute_margin_pivot_sku_canal(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot marge brute % : lignes = SKUs, colonnes = canaux.

    Permet d'identifier d'un coup d'oeil les combinaisons SKU/canal
    les plus rentables et celles à risque.

    Returns:
        DataFrame pivot (marge_brute_pct moyenne), index = sku_id.
    """
    pivot = df.pivot_table(
        index="sku_id",
        columns="canal",
        values="marge_brute_pct",
        aggfunc="mean",
    ).round(4)

    logger.info(
        "Pivot SKU × Canal : {} SKUs × {} canaux",
        pivot.shape[0], pivot.shape[1]
    )
    return pivot


# ── Export parquets ───────────────────────────────────────────────────────────
def export_margin_outputs(
    df: pd.DataFrame,
    output_dir: str,
) -> None:
    """Calcule et exporte les 4 sorties marge en parquet.

    Args:
        df: DataFrame des transactions.
        output_dir: Dossier cible (ex. 'data/processed').
    """
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    compute_margin_by_sku(df).to_parquet(
        out / "margins_by_sku.parquet", index=False
    )
    compute_margin_by_channel(df).to_parquet(
        out / "margins_by_channel.parquet", index=False
    )
    compute_margin_by_region(df).to_parquet(
        out / "margins_by_region.parquet", index=False
    )
    compute_margin_by_family(df).to_parquet(
        out / "margins_by_family.parquet", index=False
    )
    compute_margin_pivot_sku_canal(df).reset_index().to_parquet(
        out / "margin_pivot_sku_canal.parquet", index=False
    )

    logger.success("Exports marges → {}", out)
