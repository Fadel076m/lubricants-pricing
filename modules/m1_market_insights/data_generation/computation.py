"""Computation functions for COGS, pricing, volume, and competitive index."""
import numpy as np
from .macro import _SEASONALITY
from .config import N_MONTHS

def _compute_cogs(
    base_oil_usd_l: float,
    brent_usd: float,
    taux_usd_local: float,
    rng: np.random.Generator,
) -> dict[str, float]:
    """Compute COGS 5-component breakdown in local currency.

    Strategy: sample target ratios within the business ranges defined in
    ANTIGRAVITY_PROMPT.md, normalize to 100%, then derive all components
    from the base oil cost.  This guarantees both realistic absolute
    values (driven by Brent + FX) AND correct ratio structure.

    Args:
        base_oil_usd_l: Base oil cost in USD/L at Brent = $80 reference.
        brent_usd: Current month Brent price in USD/barrel.
        taux_usd_local: Exchange rate USD → local currency.
        rng: Random generator.

    Returns:
        Dict with 5 COGS components + cogs_total, all in local currency.
    """
    # ── Sample target ratios within business ranges ──
    r_base = rng.uniform(0.58, 0.72)
    r_addi = rng.uniform(0.20, 0.28)
    r_pkg = rng.uniform(0.05, 0.07)
    r_tran = rng.uniform(0.07, 0.09)
    r_stor = rng.uniform(0.04, 0.05)

    # Normalize to sum to 1.0
    total_r = r_base + r_addi + r_pkg + r_tran + r_stor
    r_base /= total_r
    r_addi /= total_r
    r_pkg /= total_r
    r_tran /= total_r
    r_stor /= total_r

    # ── Base oil cost driven by Brent correlation ──
    brent_factor = brent_usd / 80.0
    actual_base_usd = (
        base_oil_usd_l * brent_factor * (1 + rng.normal(0, 0.02))
    )
    cout_huile_base = round(actual_base_usd * taux_usd_local, 2)

    # ── Derive total COGS and components from ratios ──
    cogs_raw = cout_huile_base / r_base
    cout_additifs = round(cogs_raw * r_addi, 2)
    cout_packaging = round(cogs_raw * r_pkg, 2)
    cout_transport = round(cogs_raw * r_tran, 2)
    cout_stockage = round(cogs_raw * r_stor, 2)

    # cogs_total = exact sum of rounded components (no drift)
    cogs_total = round(
        cout_huile_base + cout_additifs + cout_packaging
        + cout_transport + cout_stockage,
        2,
    )

    return {
        "cout_huile_base": cout_huile_base,
        "cout_additifs": cout_additifs,
        "cout_packaging": cout_packaging,
        "cout_transport": cout_transport,
        "cout_stockage": cout_stockage,
        "cogs_total": cogs_total,
    }


def _compute_pricing(
    cogs_total: float,
    channel: dict[str, object],
    rng: np.random.Generator,
) -> dict[str, float]:
    """Compute list price, channel discount, and Net Selling Price.

    Args:
        cogs_total: Total COGS in local currency per litre.
        channel: Channel configuration dict.
        rng: Random generator.

    Returns:
        Dict with prix_vente_brut, remise_pct, and nsp.
    """
    markup = float(channel["markup"]) * (1 + rng.normal(0, 0.02))
    prix_vente_brut = round(cogs_total * markup, 2)

    remise_pct = round(
        rng.uniform(
            float(channel["remise_min"]),
            float(channel["remise_max"]),
        ),
        4,
    )

    nsp = round(prix_vente_brut * (1 - remise_pct), 2)

    return {
        "prix_vente_brut": prix_vente_brut,
        "remise_pct": remise_pct,
        "nsp": nsp,
    }


def _compute_volume(
    product: dict[str, object],
    channel: dict[str, object],
    region: dict[str, object],
    month_idx: int,
    rng: np.random.Generator,
) -> int:
    """Compute monthly volume sold (litres) with seasonality and trend.

    Volume = base × channel_factor × region_factor × seasonality × trend × noise.
    Seasonality follows the Nov-Feb peak pattern typical of West African
    lubricant markets (dry season = higher fleet & construction activity).

    Args:
        product: Product catalog entry.
        channel: Channel configuration.
        region: Region configuration.
        month_idx: 0-based month index (0 = Jan 2022).
        rng: Random generator.

    Returns:
        Volume in litres (integer, minimum 10).
    """
    month_of_year = (month_idx % 12) + 1
    seasonality = _SEASONALITY[month_of_year]

    base = float(product["volume_base"])
    adjusted = (
        base
        * float(channel["volume_factor"])
        * float(region["volume_factor"])
        * seasonality
    )

    # Slight upward trend over 36 months (+3% total)
    trend = 1.0 + 0.03 * (month_idx / (N_MONTHS - 1))

    # Random noise (±10%)
    noise = 1.0 + rng.normal(0, 0.10)

    return max(10, int(adjusted * trend * noise))


def _compute_competitor_price(
    nsp: float,
    channel: dict[str, object],
    rng: np.random.Generator,
) -> float:
    """Generate realistic competitor price from channel dynamics.

    Competitor prices cluster around our NSP with spread depending on
    channel transparency: B2C has tight spreads (transparent market),
    B2B OEM has wider spreads (opaque contract pricing).

    Args:
        nsp: Our net selling price in local currency.
        channel: Channel config with price_spread.
        rng: Random generator.

    Returns:
        Competitor price in local currency.
    """
    spread = float(channel["price_spread"])
    offset = rng.normal(0, spread)
    return round(nsp * (1 + offset), 2)


def _compute_competitive_index(
    nsp: float,
    prix_concurrent: float,
    rng: np.random.Generator,
) -> float:
    """Compute competitive pressure index in [0, 1].

    0 = no pressure (we are significantly cheaper than competitors).
    1 = maximum pressure (we are significantly more expensive).

    Args:
        nsp: Our NSP in local currency.
        prix_concurrent: Competitor price in local currency.
        rng: Random generator.

    Returns:
        Float between 0 and 1, rounded to 4 decimals.
    """
    if nsp <= 0:
        return 0.5

    price_gap = (nsp - prix_concurrent) / nsp
    raw = 0.45 + price_gap * 3.5 + rng.normal(0, 0.06)
    return round(float(np.clip(raw, 0.0, 1.0)), 4)
