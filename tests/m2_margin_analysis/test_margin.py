"""Tests M2 — Margin Analysis : COGS engine, margin calculator, alerts."""

import pandas as pd
import numpy as np
import pytest

from modules.m2_margin_analysis.cogs_engine import (
    compute_cogs_breakdown,
    compute_brent_sensitivity,
    COGS_COMPONENTS,
)
from modules.m2_margin_analysis.margin_calculator import (
    compute_margin_by_sku,
    compute_margin_by_channel,
    compute_margin_by_region,
)
from modules.m2_margin_analysis.alerts import (
    classify_margin,
    THRESHOLD_RED,
    THRESHOLD_AMBER,
    STATUS_GREEN,
    STATUS_AMBER,
    STATUS_RED,
)


# ── Fixture commune ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Mini dataset (12 lignes) couvrant 2 SKUs × 3 canaux × 2 régions."""
    rng = np.random.default_rng(42)
    n = 12
    nsp             = rng.uniform(900, 1200, n)
    cout_huile_base = rng.uniform(300,  450, n)
    cout_additifs   = rng.uniform( 80,  150, n)
    cout_packaging  = rng.uniform( 30,   50, n)
    cout_transport  = rng.uniform( 40,   70, n)
    cout_stockage   = rng.uniform( 20,   40, n)
    cogs_total      = cout_huile_base + cout_additifs + cout_packaging + cout_transport + cout_stockage
    marge_brute     = nsp - cogs_total
    marge_brute_pct = marge_brute / nsp
    return pd.DataFrame({
        "sku_id":          ["SKU-A"] * 6 + ["SKU-B"] * 6,
        "produit":         ["Huile 5W30 1L"] * 6 + ["Huile 10W40 5L"] * 6,
        "famille":         ["Moteur"] * 12,
        "canal":           (["B2C GMS", "B2B Industrie", "B2B OEM"] * 2 +
                            ["B2C GMS", "B2B Industrie", "B2B OEM"] * 2),
        "region":          (["Dakar-SN"] * 3 + ["Abidjan-CI"] * 3) * 2,
        "devise_locale":   ["XOF"] * n,
        "taux_usd_local":  rng.uniform(580, 620, n),
        "nsp":             nsp,
        "cogs_total":      cogs_total,
        "marge_brute":     marge_brute,
        "marge_brute_pct": marge_brute_pct,
        "volume_vendu":    rng.integers(100, 500, n),
        "cout_huile_base": cout_huile_base,
        "cout_additifs":   cout_additifs,
        "cout_packaging":  cout_packaging,
        "cout_transport":  cout_transport,
        "cout_stockage":   cout_stockage,
        "prix_brent_usd":  [80.0] * 6 + [90.0] * 6,
    })


# ── Tests : cogs_engine ───────────────────────────────────────────────────────

class TestCogsBreakdown:
    def test_returns_dataframe(self, sample_df):
        result = compute_cogs_breakdown(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_global_breakdown_has_all_components(self, sample_df):
        result = compute_cogs_breakdown(sample_df)
        assert "poste" in result.columns
        postes = set(result["poste"].tolist())
        assert postes == set(COGS_COMPONENTS)

    def test_breakdown_by_canal(self, sample_df):
        result = compute_cogs_breakdown(sample_df, group_by="canal")
        assert "canal" in result.columns
        assert len(result) > 0

    def test_part_pct_sums_near_100_per_group(self, sample_df):
        result = compute_cogs_breakdown(sample_df, group_by="canal")
        totals = result.groupby("canal")["part_pct_cogs"].sum()
        assert (totals.between(0.99, 1.01)).all(), f"Sommes: {totals.tolist()}"

    def test_invalid_group_raises(self, sample_df):
        with pytest.raises(ValueError, match="group_by"):
            compute_cogs_breakdown(sample_df, group_by="invalid_col")


class TestBrentSensitivity:
    def test_returns_dataframe(self, sample_df):
        result = compute_brent_sensitivity(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self, sample_df):
        result = compute_brent_sensitivity(sample_df)
        required = {"canal", "marge_actuelle_pct", "marge_choc_pct", "delta_pts"}
        assert required.issubset(result.columns)

    def test_positive_brent_shock_reduces_margin(self, sample_df):
        result = compute_brent_sensitivity(sample_df, brent_shock_pct=0.10)
        assert (result["delta_pts"] < 0).all()


# ── Tests : margin_calculator ─────────────────────────────────────────────────

class TestMarginBySku:
    def test_returns_dataframe_with_all_skus(self, sample_df):
        result = compute_margin_by_sku(sample_df)
        assert set(result["sku_id"]) == {"SKU-A", "SKU-B"}

    def test_sorted_ascending(self, sample_df):
        result = compute_margin_by_sku(sample_df)
        marges = result["marge_brute_pct_moy"].tolist()
        assert marges == sorted(marges)

    def test_required_columns(self, sample_df):
        result = compute_margin_by_sku(sample_df)
        for col in ("marge_brute_pct_moy", "nsp_moy", "cogs_moy", "volume_total"):
            assert col in result.columns


class TestMarginByChannel:
    def test_has_contribution_col(self, sample_df):
        result = compute_margin_by_channel(sample_df)
        assert "contribution_ca_pct" in result.columns

    def test_contributions_sum_to_100(self, sample_df):
        result = compute_margin_by_channel(sample_df)
        total = result["contribution_ca_pct"].sum()
        assert abs(total - 1.0) < 0.01

    def test_all_canaux_present(self, sample_df):
        result = compute_margin_by_channel(sample_df)
        assert set(result["canal"]) == {"B2C GMS", "B2B Industrie", "B2B OEM"}


class TestMarginByRegion:
    def test_returns_one_row_per_region(self, sample_df):
        result = compute_margin_by_region(sample_df)
        assert len(result) == 2  # Dakar-SN + Abidjan-CI

    def test_marge_within_valid_range(self, sample_df):
        result = compute_margin_by_region(sample_df)
        assert (result["marge_brute_pct_moy"].between(0, 1)).all()


# ── Tests : alerts ────────────────────────────────────────────────────────────

class TestClassifyMargin:
    def test_green_above_threshold(self):
        df = pd.DataFrame({"marge_brute_pct": [0.35, 0.40, 0.50]})
        result = classify_margin(df)
        assert (result["statut_marge"] == STATUS_GREEN).all()

    def test_amber_between_thresholds(self):
        df = pd.DataFrame({"marge_brute_pct": [0.20, 0.25, 0.29]})
        result = classify_margin(df)
        assert (result["statut_marge"] == STATUS_AMBER).all()

    def test_red_below_threshold(self):
        df = pd.DataFrame({"marge_brute_pct": [0.05, 0.10, 0.19]})
        result = classify_margin(df)
        assert (result["statut_marge"] == STATUS_RED).all()

    def test_does_not_mutate_input(self):
        df = pd.DataFrame({"marge_brute_pct": [0.25]})
        original_cols = list(df.columns)
        classify_margin(df)
        assert list(df.columns) == original_cols

    def test_exact_thresholds(self):
        # Boundaries are exclusive (<), so values just below each threshold
        # should be classified into the lower bucket.
        df = pd.DataFrame({"marge_brute_pct": [THRESHOLD_RED - 0.001, THRESHOLD_AMBER - 0.001]})
        result = classify_margin(df)
        assert result.iloc[0]["statut_marge"] == STATUS_RED
        assert result.iloc[1]["statut_marge"] == STATUS_AMBER
