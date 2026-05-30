"""M2 — Margin Analysis package."""
from .cogs_engine import compute_cogs_breakdown, compute_brent_sensitivity
from .margin_calculator import (
    compute_margin_by_sku,
    compute_margin_by_channel,
    compute_margin_by_region,
    compute_margin_by_family,
    compute_margin_pivot_sku_canal,
)
from .alerts import classify_margin, get_sku_alerts, compute_alert_summary

__all__ = [
    "compute_cogs_breakdown",
    "compute_brent_sensitivity",
    "compute_margin_by_sku",
    "compute_margin_by_channel",
    "compute_margin_by_region",
    "compute_margin_by_family",
    "compute_margin_pivot_sku_canal",
    "classify_margin",
    "get_sku_alerts",
    "compute_alert_summary",
]
