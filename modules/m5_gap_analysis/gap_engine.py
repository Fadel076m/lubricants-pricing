"""Gap Engine — M5 Gap Analysis.

Calcule les écarts (Réel - Prévu) sur trois axes : volume, NSP, marge.
Dimensions d'analyse : global, SKU, canal, région, mois.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

# Seuils de classification des gaps
GAP_FAVORABLE   =  0.05   # > +5%  → Favorable
GAP_DEFAVORABLE = -0.05   # < -5%  → Défavorable
GAP_CRITIQUE    = -0.10   # < -10% → Critique

STATUS_FAVORABLE  = "FAVORABLE"
STATUS_IN_TARGET  = "DANS CIBLE"
STATUS_DEFAV      = "DÉFAVORABLE"
STATUS_CRITIQUE   = "CRITIQUE"

TARGETS = ["volume_vendu", "nsp", "marge_brute_pct"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _classify_gap(gap_rel: float) -> str:
    if gap_rel > GAP_FAVORABLE:
        return STATUS_FAVORABLE
    if gap_rel < GAP_CRITIQUE:
        return STATUS_CRITIQUE
    if gap_rel < GAP_DEFAVORABLE:
        return STATUS_DEFAV
    return STATUS_IN_TARGET


def _add_gap_columns(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """Ajoute gap_abs, gap_rel et statut_gap pour une cible donnée."""
    df = df.copy()
    df["gap_abs"] = df["reel"] - df["prevu"]
    df["gap_rel"] = df["gap_abs"] / df["prevu"].replace(0, float("nan"))
    df["statut_gap"] = df["gap_rel"].apply(_classify_gap)
    df["target"] = target
    return df


# ── Agrégation réel mensuelle ─────────────────────────────────────────────────

def _build_real_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les transactions en mensuel (identique à M4 _features.py)."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    agg = df.groupby("month").agg(
        volume_vendu   =("volume_vendu",     "sum"),
        nsp            =("nsp",              "mean"),
        marge_brute_pct=("marge_brute_pct",  "mean"),
    ).reset_index().rename(columns={"month": "date"})
    return agg


def _build_real_monthly_by(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Agrège par dimension (sku_code | canal | region)."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    agg = df.groupby(["month", by]).agg(
        volume_vendu   =("volume_vendu",     "sum"),
        nsp            =("nsp",              "mean"),
        marge_brute_pct=("marge_brute_pct",  "mean"),
    ).reset_index().rename(columns={"month": "date"})
    return agg


# ── Gap global (une seule valeur par cible × horizon) ────────────────────────

def compute_gap_global(
    df_real: pd.DataFrame,
    forecasts_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compare les agrégats globaux réels vs les prévisions M4 (horizon 30j).

    Retourne un DataFrame :
        target | prevu | reel | gap_abs | gap_rel | statut_gap
    """
    real_monthly = _build_real_monthly(df_real)
    last_real    = real_monthly.iloc[-1]

    rows = []
    for target in TARGETS:
        fc = forecasts_df[
            (forecasts_df["target"] == target) &
            (forecasts_df["horizon_days"] == 30)
        ]
        if fc.empty:
            continue
        prevu = float(fc["yhat"].iloc[0])
        reel  = float(last_real[target])
        rows.append({"target": target, "prevu": prevu, "reel": reel})

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    out["gap_abs"] = out["reel"] - out["prevu"]
    out["gap_rel"] = out["gap_abs"] / out["prevu"].replace(0, float("nan"))
    out["statut_gap"] = out["gap_rel"].apply(_classify_gap)
    return out


# ── Gap par mois ──────────────────────────────────────────────────────────────

def compute_gap_by_month(
    df_real: pd.DataFrame,
    forecasts_df: pd.DataFrame,
) -> pd.DataFrame:
    """Associe chaque horizon de forecast (30/60/90j) au mois correspondant.

    Retourne : date | target | prevu | reel | gap_abs | gap_rel | statut_gap
    """
    real_monthly = _build_real_monthly(df_real)
    frames = []

    for target in TARGETS:
        fc = forecasts_df[forecasts_df["target"] == target].copy()
        fc = fc.sort_values("horizon_days").reset_index(drop=True)

        for _, row in fc.iterrows():
            fc_date = pd.to_datetime(row["ds"]) if "ds" in row else None
            if fc_date is None:
                continue
            # Chercher le mois réel le plus proche
            real_row = real_monthly[real_monthly["date"] <= fc_date]
            if real_row.empty:
                continue
            real_val = float(real_row.iloc[-1][target])
            frames.append({
                "date":         fc_date,
                "horizon_days": int(row["horizon_days"]),
                "target":       target,
                "prevu":        float(row["yhat"]),
                "reel":         real_val,
                "best_model":   row.get("best_model", ""),
            })

    if not frames:
        return pd.DataFrame()

    out = pd.DataFrame(frames)
    out["gap_abs"] = out["reel"] - out["prevu"]
    out["gap_rel"] = out["gap_abs"] / out["prevu"].replace(0, float("nan"))
    out["statut_gap"] = out["gap_rel"].apply(_classify_gap)
    return out


# ── Gap par SKU ───────────────────────────────────────────────────────────────

def compute_gap_by_sku(df_real: pd.DataFrame) -> pd.DataFrame:
    """Gap sur volume mensuel par SKU.

    Utilise la moyenne mensuelle comme "prévu" (benchmark interne)
    et compare chaque mois individuel au benchmark.

    Retourne : sku_id | date | prevu | reel | gap_abs | gap_rel | statut_gap
    """
    by = "sku_id"
    real_by = _build_real_monthly_by(df_real, by)

    frames = []
    for target in ["volume_vendu"]:  # SKU principalement pertinent sur volume
        grp = real_by.groupby(by)[target]
        benchmark = grp.transform("mean")
        sub = real_by[[by, "date", target]].copy()
        sub["prevu"]  = benchmark.values
        sub["reel"]   = sub[target]
        sub["target"] = target
        frames.append(sub[[by, "date", "target", "prevu", "reel"]])

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out["gap_abs"] = out["reel"] - out["prevu"]
    out["gap_rel"] = out["gap_abs"] / out["prevu"].replace(0, float("nan"))
    out["statut_gap"] = out["gap_rel"].apply(_classify_gap)
    # Rename generic key to sku_code for downstream compatibility
    out = out.rename(columns={by: "sku_code"})
    return out.sort_values("gap_rel").reset_index(drop=True)


# ── Gap par canal ─────────────────────────────────────────────────────────────

def compute_gap_by_canal(df_real: pd.DataFrame) -> pd.DataFrame:
    """Gap sur volume + NSP par canal de distribution."""
    by = "canal"
    real_by = _build_real_monthly_by(df_real, by)

    frames = []
    for target in ["volume_vendu", "nsp", "marge_brute_pct"]:
        grp = real_by.groupby(by)[target]
        benchmark = grp.transform("mean")
        sub = real_by[[by, "date", target]].copy()
        sub["prevu"]  = benchmark.values
        sub["reel"]   = sub[target]
        sub["target"] = target
        frames.append(sub[[by, "date", "target", "prevu", "reel"]])

    out = pd.concat(frames, ignore_index=True)
    out["gap_abs"] = out["reel"] - out["prevu"]
    out["gap_rel"] = out["gap_abs"] / out["prevu"].replace(0, float("nan"))
    out["statut_gap"] = out["gap_rel"].apply(_classify_gap)
    return out.sort_values("gap_rel").reset_index(drop=True)


# ── Gap par région ────────────────────────────────────────────────────────────

def compute_gap_by_region(df_real: pd.DataFrame) -> pd.DataFrame:
    """Gap sur volume + NSP par région géographique."""
    by = "region"
    real_by = _build_real_monthly_by(df_real, by)

    frames = []
    for target in ["volume_vendu", "nsp", "marge_brute_pct"]:
        grp = real_by.groupby(by)[target]
        benchmark = grp.transform("mean")
        sub = real_by[[by, "date", target]].copy()
        sub["prevu"]  = benchmark.values
        sub["reel"]   = sub[target]
        sub["target"] = target
        frames.append(sub[[by, "date", "target", "prevu", "reel"]])

    out = pd.concat(frames, ignore_index=True)
    out["gap_abs"] = out["reel"] - out["prevu"]
    out["gap_rel"] = out["gap_abs"] / out["prevu"].replace(0, float("nan"))
    out["statut_gap"] = out["gap_rel"].apply(_classify_gap)
    return out.sort_values("gap_rel").reset_index(drop=True)


# ── Export ────────────────────────────────────────────────────────────────────

def export_gap_outputs(
    gap_results: dict[str, pd.DataFrame],
    output_dir: str,
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for name, df in gap_results.items():
        if df is not None and not df.empty:
            path = out / f"gap_{name}.parquet"
            df.to_parquet(path, index=False)
            logger.info("  → {}", path.name)

    logger.success("Exports Gap Analysis → {}", out)
