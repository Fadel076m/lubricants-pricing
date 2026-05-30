"""COGS decomposition engine — M2 Margin Analysis.

Pourquoi ce fichier ?
    Un Pricing Manager doit comprendre POURQUOI sa marge est là où elle est.
    Ce module décompose le COGS en ses 5 postes pour identifier le levier
    le plus impactant, et quantifie l'exposition au risque Brent — variable
    de risque COGS centrale sur les marchés Afrique de l'Ouest.
"""

import pandas as pd
import numpy as np
from loguru import logger

# ── Constantes ────────────────────────────────────────────────────────────────
COGS_COMPONENTS: list[str] = [
    "cout_huile_base",
    "cout_additifs",
    "cout_packaging",
    "cout_transport",
    "cout_stockage",
]

COMPONENT_LABELS: dict[str, str] = {
    "cout_huile_base": "Huile de base",
    "cout_additifs":   "Additifs",
    "cout_packaging":  "Packaging",
    "cout_transport":  "Transport",
    "cout_stockage":   "Stockage",
}

VALID_GROUP_KEYS: frozenset[str] = frozenset({"famille", "canal", "region"})


# ── Décomposition COGS ────────────────────────────────────────────────────────
def compute_cogs_breakdown(
    df: pd.DataFrame,
    group_by: str | None = None,
) -> pd.DataFrame:
    """Décompose le COGS en 5 postes, globalement ou par dimension.

    Args:
        df: DataFrame des transactions (24 colonnes).
        group_by: Dimension d'agrégation — 'famille', 'canal', 'region',
            ou None pour la décomposition globale.

    Returns:
        DataFrame avec colonnes :
            [group (si group_by fourni), poste, label, valeur_moyenne, part_pct_cogs]
    """
    if group_by is not None and group_by not in VALID_GROUP_KEYS:
        raise ValueError(
            f"group_by doit être None ou l'une de {VALID_GROUP_KEYS}, "
            f"reçu : '{group_by}'"
        )

    records: list[dict] = []

    if group_by is None:
        avg_total = df["cogs_total"].mean()
        for col in COGS_COMPONENTS:
            avg = df[col].mean()
            records.append({
                "poste":         col,
                "label":         COMPONENT_LABELS[col],
                "valeur_moyenne": round(avg, 2),
                "part_pct_cogs": round(avg / avg_total, 4) if avg_total > 0 else 0.0,
            })
    else:
        for grp_val, grp_df in df.groupby(group_by):
            avg_total = grp_df["cogs_total"].mean()
            for col in COGS_COMPONENTS:
                avg = grp_df[col].mean()
                records.append({
                    group_by:        grp_val,
                    "poste":         col,
                    "label":         COMPONENT_LABELS[col],
                    "valeur_moyenne": round(avg, 2),
                    "part_pct_cogs": round(avg / avg_total, 4) if avg_total > 0 else 0.0,
                })

    result = pd.DataFrame(records)
    logger.info(
        "COGS breakdown calculé — {} lignes (group_by={})",
        len(result), group_by or "global"
    )
    return result


def compute_cogs_share_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot : part % de chaque poste COGS par famille de produit.

    Utile pour comparer si les Graisses ont plus de coûts packaging
    que les huiles Moteur, par exemple.

    Returns:
        DataFrame pivot indexé par famille, colonnes = labels des postes,
        valeurs = part % dans le COGS (entre 0 et 1).
    """
    breakdown = compute_cogs_breakdown(df, group_by="famille")

    pivot = breakdown.pivot(
        index="famille",
        columns="label",
        values="part_pct_cogs",
    ).rename_axis(None, axis=1).reset_index()

    return pivot


# ── Sensibilité au choc Brent ─────────────────────────────────────────────────
def compute_brent_sensitivity(
    df: pd.DataFrame,
    brent_shock_pct: float = 0.10,
) -> pd.DataFrame:
    """Simule l'impact d'un choc Brent sur le COGS et la marge brute.

    Hypothèse : une variation de X % du Brent se traduit par une variation
    proportionnelle du cout_huile_base (corrélation R² = 0,98 en M1).
    Les autres postes COGS restent constants.

    Args:
        df: DataFrame des transactions.
        brent_shock_pct: Amplitude du choc relatif (défaut +10 %).
            Passer une valeur négative pour simuler une baisse.

    Returns:
        DataFrame agrégé par canal avec colonnes :
            canal | marge_actuelle_pct | marge_choc_pct | delta_pts |
            pct_records_alert_avant | pct_records_alert_apres
    """
    sim = df.copy()

    delta_huile = sim["cout_huile_base"] * brent_shock_pct
    sim["cogs_total_choc"]    = sim["cogs_total"] + delta_huile
    sim["marge_brute_choc"]   = sim["nsp"] - sim["cogs_total_choc"]
    sim["marge_pct_choc"]     = sim["marge_brute_choc"] / sim["nsp"]

    result = (
        sim.groupby("canal")
        .agg(
            marge_actuelle_pct=("marge_brute_pct",  "mean"),
            marge_choc_pct    =("marge_pct_choc",   "mean"),
            n_total           =("nsp",               "count"),
            n_alert_avant     =("marge_brute_pct",   lambda s: (s < 0.20).sum()),
            n_alert_apres     =("marge_pct_choc",    lambda s: (s < 0.20).sum()),
        )
        .reset_index()
    )

    result["delta_pts"]              = (result["marge_choc_pct"] - result["marge_actuelle_pct"]).round(4)
    result["pct_records_alert_avant"] = (result["n_alert_avant"] / result["n_total"]).round(4)
    result["pct_records_alert_apres"] = (result["n_alert_apres"] / result["n_total"]).round(4)

    result = result.drop(columns=["n_total", "n_alert_avant", "n_alert_apres"])
    result = result.round({"marge_actuelle_pct": 4, "marge_choc_pct": 4})

    logger.info(
        "Sensibilité Brent calculée — choc {:+.0%} — {} canaux analysés",
        brent_shock_pct, len(result)
    )
    return result


# ── Export parquets ───────────────────────────────────────────────────────────
def export_cogs_outputs(
    df: pd.DataFrame,
    output_dir: str,
) -> None:
    """Calcule et exporte les 3 sorties COGS en parquet.

    Args:
        df: DataFrame des transactions.
        output_dir: Dossier cible (ex. 'data/processed').
    """
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    breakdown_global = compute_cogs_breakdown(df)
    breakdown_canal  = compute_cogs_breakdown(df, group_by="canal")
    share_pivot      = compute_cogs_share_pivot(df)
    sensitivity_10   = compute_brent_sensitivity(df, brent_shock_pct=0.10)

    breakdown_global.to_parquet(out / "cogs_breakdown.parquet",         index=False)
    breakdown_canal.to_parquet( out / "cogs_breakdown_canal.parquet",   index=False)
    share_pivot.to_parquet(     out / "cogs_share_famille.parquet",     index=False)
    sensitivity_10.to_parquet(  out / "cogs_brent_sensitivity.parquet", index=False)

    logger.success("Exports COGS → {}", out)
