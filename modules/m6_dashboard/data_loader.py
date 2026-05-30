"""Centralized data loader for M6 Dashboard.

Charge et met en cache tous les parquets une seule fois au démarrage.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
from loguru import logger

_ROOT = Path(__file__).resolve().parents[2]
_SYN  = _ROOT / "data" / "synthetic"
_PROC = _ROOT / "data" / "processed"


def _load(path: Path) -> pd.DataFrame | None:
    if path.exists():
        return pd.read_parquet(path)
    logger.warning("Fichier absent : {} — certains graphiques seront vides.", path.name)
    return None


@lru_cache(maxsize=1)
def load_all() -> dict[str, pd.DataFrame | None]:
    """Charge tous les datasets au premier appel, puis utilise le cache."""
    raw = _load(_SYN / "transactions.parquet")

    data = {
        "raw":        raw,
        "forecasts":  _load(_PROC / "forecasts_30_60_90.parquet"),
        "metrics":    _load(_PROC / "model_metrics.parquet"),
        "monthly":    _load(_PROC / "monthly_aggregates.parquet"),
        "gap_global": _load(_PROC / "gap_global.parquet"),
        "gap_sku":    _load(_PROC / "gap_sku.parquet"),
        "gap_canal":  _load(_PROC / "gap_canal.parquet"),
        "gap_region": _load(_PROC / "gap_region.parquet"),
        "cogs":       _load(_PROC / "cogs_breakdown.parquet"),
        "margins":    _load(_PROC / "margins_by_sku.parquet"),
        "scenarios":  _load(_PROC / "scenario_results.parquet"),
        "pi_reco":    _load(_PROC / "pi_recommendations.parquet"),
    }

    # Enrichissement de base sur raw
    if raw is not None:
        raw["date"] = pd.to_datetime(raw["date"])
        raw["month"] = raw["date"].dt.to_period("M").dt.to_timestamp()
        raw["ca"] = raw["nsp"] * raw["volume_vendu"]

    logger.info("DataLoader : {} datasets chargés.", sum(v is not None for v in data.values()))
    return data


def get_kpi_global(raw: pd.DataFrame) -> dict:
    """KPIs globaux pour la page Executive (fonctionne sur n'importe quel sous-ensemble filtré)."""
    if raw is None or raw.empty:
        return {}

    months_sorted = sorted(raw["month"].unique())
    last_month = months_sorted[-1]
    prev_month = months_sorted[-2] if len(months_sorted) > 1 else last_month

    cur  = raw[raw["month"] == last_month]
    prev = raw[raw["month"] == prev_month]

    def _delta(cur_val, prev_val):
        if prev_val == 0:
            return 0.0
        return (cur_val - prev_val) / prev_val * 100

    ca_cur   = cur["ca"].sum()
    ca_prev  = prev["ca"].sum()
    vol_cur  = cur["volume_vendu"].sum()
    vol_prev = prev["volume_vendu"].sum()
    mg_cur   = cur["marge_brute_pct"].mean() * 100
    mg_prev  = prev["marge_brute_pct"].mean() * 100
    nsp_cur  = cur["nsp"].mean()
    nsp_prev = prev["nsp"].mean()

    return {
        "ca":           ca_cur,
        "ca_delta":     _delta(ca_cur, ca_prev),
        "volume":       vol_cur,
        "volume_delta": _delta(vol_cur, vol_prev),
        "marge":        mg_cur,
        "marge_delta":  mg_cur - mg_prev,
        "nsp":          nsp_cur,
        "nsp_delta":    _delta(nsp_cur, nsp_prev),
        "month_label":  last_month.strftime("%B %Y"),
    }
