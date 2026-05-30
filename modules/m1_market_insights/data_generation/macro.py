"""Macro-economic series generation."""
from typing import Final
import numpy as np
import pandas as pd
from .config import START_DATE, END_DATE, N_MONTHS

_BRENT_MONTHLY: Final[list[float]] = [
    # 2022: Ukraine-war spike Q1-Q2, gradual decline H2
    86.5, 94.0, 112.0, 105.5, 110.0, 117.0,
    105.0, 97.0, 88.0, 93.5, 86.0, 80.0,
    # 2023: Moderate, OPEC+ cuts boost Q3
    83.0, 83.5, 78.0, 81.0, 75.5, 74.5,
    80.0, 85.5, 93.5, 88.0, 82.0, 77.0,
    # 2024: Gradual easing, demand-side concerns
    79.0, 82.0, 85.0, 89.0, 82.5, 81.0,
    82.0, 78.5, 73.5, 75.0, 73.0, 74.0,
]

# USD/XOF — CFA franc (UEMOA), pegged to EUR at 655.957 XOF/EUR
_USD_XOF_MONTHLY: Final[list[float]] = [
    # 2022: EUR weakness → CFA weakness vs USD
    618, 622, 635, 640, 648, 655,
    660, 658, 652, 650, 645, 640,
    # 2023: EUR partial recovery
    632, 628, 620, 615, 610, 608,
    605, 610, 615, 612, 605, 600,
    # 2024: Relative stability
    602, 605, 608, 610, 607, 605,
    602, 600, 598, 595, 597, 598,
]

# USD/MAD — Moroccan Dirham (managed float, band ±5% around EUR)
_USD_MAD_MONTHLY: Final[list[float]] = [
    # 2022: MAD weakened with global USD strength
    10.05, 10.10, 10.25, 10.35, 10.45, 10.55,
    10.60, 10.50, 10.40, 10.35, 10.25, 10.15,
    # 2023: Gradual MAD recovery
    10.10, 10.05, 9.95, 9.90, 9.85, 9.80,
    9.75, 9.80, 9.85, 9.82, 9.75, 9.70,
    # 2024: Stability
    9.72, 9.75, 9.80, 9.85, 9.82, 9.78,
    9.75, 9.72, 9.68, 9.65, 9.67, 9.68,
]

# Annual inflation (%) — anchor points for interpolation
# Format: [Jan-2022, Dec-2022, Jan-2023, Dec-2023, Jan-2024, Dec-2024]
_INFLATION_ANCHORS: Final[dict[str, list[float]]] = {
    "SN": [9.7, 8.0, 5.5, 4.0, 3.2, 2.8],
    "CI": [5.3, 4.5, 4.4, 3.8, 3.8, 3.2],
    "CM": [6.3, 5.5, 7.2, 6.0, 5.5, 4.8],
    "MA": [6.6, 5.8, 6.1, 4.5, 2.5, 2.0],
}

# Lubricant demand seasonality — peaks Nov-Feb (dry season in West Africa)
# Construction, fleet maintenance, and agricultural activity drive demand up.
_SEASONALITY: Final[dict[int, float]] = {
    1: 1.20,   # Jan — peak continues, fleet activity
    2: 1.15,   # Feb — peak winding down
    3: 1.05,   # Mar — transition to normal
    4: 1.00,   # Apr — normal baseline
    5: 0.88,   # May — rainy season begins
    6: 0.85,   # Jun — low season trough
    7: 0.87,   # Jul — low season
    8: 0.90,   # Aug — low season ending
    9: 1.00,   # Sep — transition back up
    10: 1.05,  # Oct — demand building
    11: 1.18,  # Nov — dry season starts, peak begins
    12: 1.22,  # Dec — peak (fleet prep for year-end)
}

def _build_macro_series(rng: np.random.Generator) -> pd.DataFrame:
    """Build monthly macroeconomic series with realistic noise.

    Constructs 36 months of Brent prices, FX rates (USD/XOF, USD/XAF,
    USD/MAD), and inflation per country by interpolating anchor points
    and adding calibrated noise.

    Args:
        rng: NumPy random generator for reproducibility.

    Returns:
        DataFrame with 36 rows, one per month from 2022-01 to 2024-12.
    """
    dates = pd.period_range(START_DATE, END_DATE, freq="M")
    interp_x = [0, 11, 12, 23, 24, 35]

    # Interpolate inflation between anchor points + noise
    inflation: dict[str, np.ndarray] = {}
    for code, anchors in _INFLATION_ANCHORS.items():
        values = np.interp(range(N_MONTHS), interp_x, anchors)
        inflation[code] = np.round(
            values + rng.normal(0, 0.2, N_MONTHS), 1
        )

    # XAF is pegged to EUR at same rate as XOF (both CFA francs)
    usd_xof = (
        np.array(_USD_XOF_MONTHLY, dtype=float)
        + rng.normal(0, 2.5, N_MONTHS)
    )
    usd_xaf = usd_xof * (1 + rng.normal(0, 0.001, N_MONTHS))

    return pd.DataFrame({
        "date": [p.strftime("%Y-%m") for p in dates],
        "month_idx": range(N_MONTHS),
        "prix_brent_usd": np.round(
            np.array(_BRENT_MONTHLY, dtype=float)
            + rng.normal(0, 1.2, N_MONTHS),
            2,
        ),
        "taux_usd_xof": np.round(usd_xof, 2),
        "taux_usd_xaf": np.round(usd_xaf, 2),
        "taux_usd_mad": np.round(
            np.array(_USD_MAD_MONTHLY, dtype=float)
            + rng.normal(0, 0.04, N_MONTHS),
            2,
        ),
        "inflation_SN": inflation["SN"],
        "inflation_CI": inflation["CI"],
        "inflation_CM": inflation["CM"],
        "inflation_MA": inflation["MA"],
    })
