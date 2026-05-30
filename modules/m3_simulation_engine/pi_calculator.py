"""PI (Price Increase) calculator — M3 Pricing Simulation Engine.

Pourquoi ce fichier ?
    Face à un choc COGS (hausse Brent), un Pricing Manager doit quantifier
    le PI minimum pour défendre sa marge cible — sans sur-corriger au risque
    de perdre du volume. Ce module donne la réponse exacte, SKU par SKU
    et canal par canal.

Formule exacte (dérivée) :
    COGS_new    = COGS + cout_huile_base × brent_shock_pct
    NSP_cible   = COGS_new / (1 − marge_cible)
    PI_requis   = NSP_cible / NSP − 1
"""

import pandas as pd
from loguru import logger


def compute_pi_scalar(
    nsp: float,
    cogs: float,
    cout_huile_base: float,
    brent_shock_pct: float = 0.10,
    target_margin_pct: float | None = None,
) -> dict[str, float]:
    """Calcule le PI requis pour une combinaison NSP/COGS donnée.

    Args:
        nsp: Net Selling Price actuel (devise locale/L).
        cogs: COGS total actuel (devise locale/L).
        cout_huile_base: Poste huile de base dans le COGS (devise locale/L).
        brent_shock_pct: Amplitude du choc Brent (défaut +10 %).
        target_margin_pct: Marge cible après PI. Si None, on maintient
            la marge actuelle (défense de marge).

    Returns:
        Dict avec : marge_avant, delta_cogs, cogs_apres_choc,
                    marge_sans_pi, marge_cible, pi_requis, nsp_cible.
    """
    marge_avant = (nsp - cogs) / nsp if nsp > 0 else 0.0

    if target_margin_pct is None:
        target_margin_pct = marge_avant

    delta_cogs   = cout_huile_base * brent_shock_pct
    cogs_new     = cogs + delta_cogs
    marge_sans_pi = (nsp - cogs_new) / nsp if nsp > 0 else 0.0

    # NSP_cible = COGS_new / (1 - marge_cible)
    denominator = 1.0 - target_margin_pct
    if denominator <= 0:
        pi_requis = 0.0
        nsp_cible = nsp
    else:
        nsp_cible = cogs_new / denominator
        pi_requis = max(0.0, (nsp_cible / nsp) - 1) if nsp > 0 else 0.0

    return {
        "marge_avant":    round(marge_avant, 4),
        "delta_cogs":     round(delta_cogs, 2),
        "cogs_apres_choc": round(cogs_new, 2),
        "marge_sans_pi":  round(marge_sans_pi, 4),
        "marge_cible":    round(target_margin_pct, 4),
        "pi_requis":      round(pi_requis, 4),
        "nsp_cible":      round(nsp_cible, 2),
    }


def compute_pi_recommendations(
    df: pd.DataFrame,
    brent_shock_pct: float = 0.10,
    target_margin_pct: float | None = None,
) -> pd.DataFrame:
    """Calcule le PI requis pour chaque combinaison SKU × Canal.

    Args:
        df: DataFrame des transactions brutes.
        brent_shock_pct: Amplitude du choc Brent.
        target_margin_pct: Marge cible. None = défense de la marge actuelle.

    Returns:
        DataFrame trié par pi_requis décroissant, colonnes :
            sku_id | produit | famille | canal | nsp_moy | cogs_moy |
            cout_huile_base_moy | marge_avant | marge_sans_pi |
            pi_requis | nsp_cible | delta_cogs | urgence
    """
    agg = (
        df.groupby(["sku_id", "produit", "famille", "canal"])
        .agg(
            nsp_moy              =("nsp",             "mean"),
            cogs_moy             =("cogs_total",      "mean"),
            cout_huile_base_moy  =("cout_huile_base", "mean"),
            volume_moy           =("volume_vendu",    "mean"),
        )
        .reset_index()
    )

    rows = []
    for _, row in agg.iterrows():
        pi_info = compute_pi_scalar(
            nsp=row["nsp_moy"],
            cogs=row["cogs_moy"],
            cout_huile_base=row["cout_huile_base_moy"],
            brent_shock_pct=brent_shock_pct,
            target_margin_pct=target_margin_pct,
        )
        rows.append({**row.to_dict(), **pi_info})

    result = pd.DataFrame(rows)

    # Urgence : basée sur la marge sans PI
    result["urgence"] = "FAIBLE"
    result.loc[result["marge_sans_pi"] < 0.25, "urgence"] = "MODÉRÉE"
    result.loc[result["marge_sans_pi"] < 0.20, "urgence"] = "ÉLEVÉE"
    result.loc[result["marge_sans_pi"] < 0.10, "urgence"] = "CRITIQUE"

    result = (
        result
        .sort_values("pi_requis", ascending=False)
        .round({
            "nsp_moy": 2, "cogs_moy": 2, "cout_huile_base_moy": 2,
            "marge_avant": 4, "marge_sans_pi": 4, "pi_requis": 4,
            "nsp_cible": 2, "delta_cogs": 2,
        })
        .reset_index(drop=True)
    )

    logger.info(
        "PI recommandations — {} combinaisons SKU×Canal | choc Brent {:+.0%}",
        len(result), brent_shock_pct
    )
    return result


def export_pi_outputs(
    df: pd.DataFrame,
    output_dir: str,
    brent_shock_pct: float = 0.10,
) -> None:
    """Exporte les recommandations PI en parquet.

    Args:
        df: DataFrame des transactions.
        output_dir: Dossier cible.
        brent_shock_pct: Amplitude du choc Brent.
    """
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    recs = compute_pi_recommendations(df, brent_shock_pct)
    recs.to_parquet(out / "pi_recommendations.parquet", index=False)
    logger.success("Export PI → {}", out / "pi_recommendations.parquet")
