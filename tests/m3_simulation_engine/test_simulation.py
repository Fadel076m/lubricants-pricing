"""Tests M3 — Simulation Engine : PI calculator, elasticity, scenario engine."""

import pandas as pd
import numpy as np
import pytest

from modules.m3_simulation_engine.pi_calculator import (
    compute_pi_scalar,
    compute_pi_recommendations,
)
from modules.m3_simulation_engine.elasticity_model import compute_volume_impact
from modules.m3_simulation_engine.scenario_engine import (
    run_single_scenario,
    SCENARIOS,
)


# ── Fixture commune ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Mini dataset (10 lignes) pour tester le moteur de simulation."""
    rng = np.random.default_rng(0)
    n = 10
    canaux = ["B2C GMS", "B2B Industrie", "B2B OEM", "Export", "B2C Réseau pétrolier"]
    return pd.DataFrame({
        "sku_id":          [f"SKU-{i}" for i in range(n)],
        "produit":         [f"Produit {i}" for i in range(n)],
        "famille":         ["Moteur"] * n,
        "canal":           (canaux * 2)[:n],
        "region":          ["Dakar-SN"] * n,
        "nsp":             rng.uniform(900, 1200, n),
        "cogs_total":      rng.uniform(600,  800, n),
        "marge_brute":     rng.uniform(200,  400, n),
        "marge_brute_pct": rng.uniform(0.22, 0.38, n),
        "volume_vendu":    rng.integers(100, 500, n),
        "cout_huile_base": rng.uniform(400, 550, n),
        "cout_additifs":   rng.uniform(100, 180, n),
        "cout_packaging":  rng.uniform( 40,  60, n),
        "cout_transport":  rng.uniform( 50,  80, n),
        "cout_stockage":   rng.uniform( 30,  50, n),
        "indice_conc":     rng.uniform(0.3,  0.7, n),
        "prix_brent_usd":  [85.0] * n,
    })


# ── Tests : compute_pi_scalar ─────────────────────────────────────────────────

class TestPiScalar:
    def test_returns_dict_with_required_keys(self):
        result = compute_pi_scalar(nsp=1000, cogs=700, cout_huile_base=450)
        required = {"marge_avant", "delta_cogs", "cogs_apres_choc",
                    "marge_sans_pi", "marge_cible", "pi_requis", "nsp_cible"}
        assert required.issubset(result.keys())

    def test_pi_requis_positive_when_brent_shock(self):
        result = compute_pi_scalar(
            nsp=1000, cogs=700, cout_huile_base=450,
            brent_shock_pct=0.10
        )
        assert result["pi_requis"] > 0

    def test_pi_requis_zero_when_no_shock(self):
        result = compute_pi_scalar(
            nsp=1000, cogs=700, cout_huile_base=450,
            brent_shock_pct=0.0
        )
        assert result["pi_requis"] == 0.0

    def test_higher_brent_shock_requires_higher_pi(self):
        pi_10 = compute_pi_scalar(1000, 700, 450, brent_shock_pct=0.10)["pi_requis"]
        pi_20 = compute_pi_scalar(1000, 700, 450, brent_shock_pct=0.20)["pi_requis"]
        assert pi_20 > pi_10

    def test_marge_avant_formula(self):
        nsp, cogs = 1000.0, 700.0
        result = compute_pi_scalar(nsp=nsp, cogs=cogs, cout_huile_base=400)
        expected_marge = (nsp - cogs) / nsp
        assert abs(result["marge_avant"] - expected_marge) < 0.001

    def test_target_margin_overrides_current(self):
        result = compute_pi_scalar(
            nsp=1000, cogs=700, cout_huile_base=450,
            brent_shock_pct=0.10, target_margin_pct=0.40
        )
        assert result["marge_cible"] == pytest.approx(0.40)

    def test_nsp_zero_returns_zero_marge(self):
        result = compute_pi_scalar(nsp=0, cogs=700, cout_huile_base=400)
        assert result["marge_avant"] == 0.0


# ── Tests : compute_volume_impact ─────────────────────────────────────────────

class TestVolumeImpact:
    def test_positive_pi_negative_elasticity_reduces_volume(self):
        vol = compute_volume_impact(base_volume=1000, pi_pct=0.05, elasticity=-0.5)
        assert vol < 1000

    def test_zero_pi_returns_base_volume(self):
        vol = compute_volume_impact(base_volume=500, pi_pct=0.0, elasticity=-1.0)
        assert vol == pytest.approx(500.0)

    def test_higher_elasticity_magnitude_loses_more_volume(self):
        vol_low  = compute_volume_impact(1000, 0.10, elasticity=-0.3)
        vol_high = compute_volume_impact(1000, 0.10, elasticity=-1.4)
        assert vol_high < vol_low

    def test_returns_float(self):
        result = compute_volume_impact(1000, 0.05, -0.5)
        assert isinstance(result, float)


# ── Tests : compute_pi_recommendations ───────────────────────────────────────

class TestPiRecommendations:
    def test_returns_dataframe(self, sample_df):
        result = compute_pi_recommendations(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_urgence_column(self, sample_df):
        result = compute_pi_recommendations(sample_df)
        assert "urgence" in result.columns

    def test_urgence_values_valid(self, sample_df):
        result = compute_pi_recommendations(sample_df)
        valid = {"FAIBLE", "MODÉRÉE", "ÉLEVÉE", "CRITIQUE"}
        assert set(result["urgence"].unique()).issubset(valid)

    def test_sorted_by_pi_descending(self, sample_df):
        result = compute_pi_recommendations(sample_df)
        pi_vals = result["pi_requis"].tolist()
        assert pi_vals == sorted(pi_vals, reverse=True)

    def test_higher_brent_shock_increases_average_pi(self, sample_df):
        pi_10 = compute_pi_recommendations(sample_df, brent_shock_pct=0.10)["pi_requis"].mean()
        pi_20 = compute_pi_recommendations(sample_df, brent_shock_pct=0.20)["pi_requis"].mean()
        assert pi_20 > pi_10


# ── Tests : scenario_engine ───────────────────────────────────────────────────

class TestScenarioEngine:
    def test_run_single_scenario_returns_dataframe(self, sample_df):
        elasticities = {"B2C GMS": -0.8, "B2B Industrie": -0.4,
                        "B2B OEM": -0.3, "Export": -0.5, "B2C Réseau pétrolier": -0.6}
        result = run_single_scenario(sample_df, elasticities, pi_pct=0.05)
        assert isinstance(result, pd.DataFrame)

    def test_positive_pi_increases_nsp(self, sample_df):
        elasticities = {c: -0.5 for c in sample_df["canal"].unique()}
        result = run_single_scenario(sample_df, elasticities, pi_pct=0.05)
        assert (result["nsp_new"] > result["nsp_baseline"]).all()

    def test_zero_pi_unchanged_nsp(self, sample_df):
        elasticities = {c: -0.5 for c in sample_df["canal"].unique()}
        result = run_single_scenario(sample_df, elasticities, pi_pct=0.00)
        assert (result["nsp_new"] == result["nsp_baseline"]).all()

    def test_scenarios_dict_has_abc(self):
        assert set(SCENARIOS.keys()) == {"A", "B", "C"}

    def test_scenario_b_has_highest_pi(self):
        pi_values = [SCENARIOS[k]["pi_pct"] for k in ["A", "B", "C"]]
        assert max(pi_values) == SCENARIOS["B"]["pi_pct"]
