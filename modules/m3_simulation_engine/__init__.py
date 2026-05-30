"""M3 — Pricing Simulation Engine package."""
from .pi_calculator import compute_pi_scalar, compute_pi_recommendations
from .elasticity_model import fit_elasticities, compute_volume_impact
from .scenario_engine import SCENARIOS, run_all_scenarios, run_monte_carlo

__all__ = [
    "compute_pi_scalar",
    "compute_pi_recommendations",
    "fit_elasticities",
    "compute_volume_impact",
    "SCENARIOS",
    "run_all_scenarios",
    "run_monte_carlo",
]
