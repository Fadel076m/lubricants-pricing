"""Margin alert detection — M2 Margin Analysis.

Pourquoi ce fichier ?
    Un Pricing Manager reçoit chaque matin un rapport d'alertes :
    quels SKUs sont sous le seuil critique, quels canaux dérivent vers
    la zone rouge. Ce fichier automatise ce diagnostic selon les 3 zones
    définies dans le README et produit une liste d'actions concrètes.

Seuils :
    ≥ 30%  → Vert  (marge saine)
    20–29% → Ambre (surveillance, PI à étudier)
    < 20%  → Rouge (action PI requise)
"""

import pandas as pd
from loguru import logger

# ── Seuils ────────────────────────────────────────────────────────────────────
THRESHOLD_RED:   float = 0.20
THRESHOLD_AMBER: float = 0.30

STATUS_GREEN = "VERT"
STATUS_AMBER = "AMBRE"
STATUS_RED   = "ROUGE"


def classify_margin(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute une colonne 'statut_marge' à chaque transaction.

    Args:
        df: DataFrame des transactions.

    Returns:
        Copie du DataFrame avec la colonne 'statut_marge' ajoutée.
    """
    out = df.copy()
    out["statut_marge"] = STATUS_GREEN
    out.loc[out["marge_brute_pct"] < THRESHOLD_AMBER, "statut_marge"] = STATUS_AMBER
    out.loc[out["marge_brute_pct"] < THRESHOLD_RED,   "statut_marge"] = STATUS_RED
    return out


def get_sku_alerts(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne les SKUs ayant au moins une transaction en zone rouge ou ambre.

    Pour chaque SKU en alerte, calcule la marge moyenne, le % de transactions
    en zone rouge, et le canal le plus problématique.

    Returns:
        DataFrame trié par % rouge décroissant, colonnes :
            sku_id | produit | famille | marge_pct_moy |
            pct_rouge | pct_ambre | canal_plus_risque | statut_dominant
    """
    classified = classify_margin(df)

    agg = (
        classified.groupby(["sku_id", "produit", "famille"])
        .agg(
            marge_pct_moy   =("marge_brute_pct",  "mean"),
            n_total         =("marge_brute_pct",  "count"),
            n_rouge         =("statut_marge",     lambda s: (s == STATUS_RED).sum()),
            n_ambre         =("statut_marge",     lambda s: (s == STATUS_AMBER).sum()),
        )
        .reset_index()
    )

    agg["pct_rouge"] = (agg["n_rouge"] / agg["n_total"]).round(4)
    agg["pct_ambre"] = (agg["n_ambre"] / agg["n_total"]).round(4)

    # Canal le plus problématique pour ce SKU
    canal_risk = (
        classified[classified["statut_marge"] == STATUS_RED]
        .groupby("sku_id")["canal"]
        .agg(lambda s: s.value_counts().index[0] if len(s) > 0 else "—")
        .rename("canal_plus_risque")
    )
    agg = agg.merge(canal_risk, on="sku_id", how="left")
    agg["canal_plus_risque"] = agg["canal_plus_risque"].fillna("—")

    # Statut dominant
    agg["statut_dominant"] = STATUS_GREEN
    agg.loc[agg["pct_ambre"] > 0,   "statut_dominant"] = STATUS_AMBER
    agg.loc[agg["pct_rouge"] > 0,   "statut_dominant"] = STATUS_RED

    alerts = (
        agg[agg["statut_dominant"] != STATUS_GREEN]
        .drop(columns=["n_total", "n_rouge", "n_ambre"])
        .sort_values("pct_rouge", ascending=False)
        .round({"marge_pct_moy": 4, "pct_rouge": 4, "pct_ambre": 4})
    )

    logger.info(
        "Alertes SKU : {} en ROUGE, {} en AMBRE",
        (alerts["statut_dominant"] == STATUS_RED).sum(),
        (alerts["statut_dominant"] == STATUS_AMBER).sum(),
    )
    return alerts


def compute_alert_summary(df: pd.DataFrame) -> dict[str, object]:
    """Résumé consolidé des alertes marge pour le rapport exécutif.

    Returns:
        Dictionnaire avec les métriques clés d'alerte :
        - n_transactions_rouge / ambre / vert
        - pct_rouge / ambre / vert
        - canal_plus_risque (celui avec le plus de transactions rouge)
        - famille_plus_risque
        - sku_plus_risque (sku_id + marge_pct_moy)
    """
    classified = classify_margin(df)
    n = len(classified)

    n_rouge = (classified["statut_marge"] == STATUS_RED).sum()
    n_ambre = (classified["statut_marge"] == STATUS_AMBER).sum()
    n_vert  = (classified["statut_marge"] == STATUS_GREEN).sum()

    rouge_df = classified[classified["statut_marge"] == STATUS_RED]

    canal_risque   = rouge_df["canal"].value_counts().index[0]   if len(rouge_df) else "—"
    famille_risque = rouge_df["famille"].value_counts().index[0] if len(rouge_df) else "—"

    sku_risque_row = (
        classified.groupby("sku_id")["marge_brute_pct"].mean()
        .sort_values()
        .iloc[0]
    )
    sku_risque_id = (
        classified.groupby("sku_id")["marge_brute_pct"].mean()
        .sort_values()
        .index[0]
    )

    summary = {
        "n_transactions_rouge":  int(n_rouge),
        "n_transactions_ambre":  int(n_ambre),
        "n_transactions_vert":   int(n_vert),
        "pct_rouge":             round(n_rouge / n, 4),
        "pct_ambre":             round(n_ambre / n, 4),
        "pct_vert":              round(n_vert  / n, 4),
        "canal_plus_risque":     canal_risque,
        "famille_plus_risque":   famille_risque,
        "sku_plus_risque":       sku_risque_id,
        "marge_sku_plus_risque": round(float(sku_risque_row), 4),
    }

    logger.info(
        "Résumé alertes — ROUGE: {:.1%} | AMBRE: {:.1%} | VERT: {:.1%}",
        summary["pct_rouge"], summary["pct_ambre"], summary["pct_vert"]
    )
    return summary


def export_alert_outputs(
    df: pd.DataFrame,
    output_dir: str,
) -> None:
    """Calcule et exporte les sorties alertes en parquet.

    Args:
        df: DataFrame des transactions.
        output_dir: Dossier cible (ex. 'data/processed').
    """
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    classified = classify_margin(df)
    classified.to_parquet(out / "transactions_classified.parquet", index=False)

    get_sku_alerts(df).to_parquet(out / "sku_alerts.parquet", index=False)

    logger.success("Exports alertes → {}", out)
