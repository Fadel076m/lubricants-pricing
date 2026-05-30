"""M5 — Gap Analysis package."""
from .gap_engine import (
    compute_gap_global,
    compute_gap_by_month,
    compute_gap_by_sku,
    compute_gap_by_canal,
    compute_gap_by_region,
    export_gap_outputs,
)
from .alerts import compute_alert_summary, get_canal_alerts, get_region_alerts
from .root_cause import generate_recommendations, get_top_critical_skus

__all__ = [
    "compute_gap_global",
    "compute_gap_by_month",
    "compute_gap_by_sku",
    "compute_gap_by_canal",
    "compute_gap_by_region",
    "export_gap_outputs",
    "compute_alert_summary",
    "get_canal_alerts",
    "get_region_alerts",
    "generate_recommendations",
    "get_top_critical_skus",
]
