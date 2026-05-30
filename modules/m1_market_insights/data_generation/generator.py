"""Main dataset generator orchestrator."""
import pandas as pd
import numpy as np
from loguru import logger
from tqdm import tqdm

from .config import SEED, N_MONTHS, EXPECTED_ROWS
from .catalog import PRODUCT_CATALOG, CHANNELS, REGIONS
from .macro import _build_macro_series
from .computation import (
    _compute_cogs,
    _compute_pricing,
    _compute_volume,
    _compute_competitor_price,
    _compute_competitive_index
)

def generate_dataset(seed: int = SEED) -> pd.DataFrame:
    """Generate the full synthetic transactions dataset.

    Iterates over all 14,400 combinations (36 months × 20 SKUs ×
    5 channels × 4 regions) and computes COGS, pricing, volume,
    and competitive metrics for each record.

    Args:
        seed: Random seed for reproducibility (default: 42).

    Returns:
        DataFrame with 14,400 rows and 24 columns matching the
        schema defined in ANTIGRAVITY_PROMPT.md.
    """
    rng = np.random.default_rng(seed)
    macro = _build_macro_series(rng)
    logger.info("Macro series built: {} months", N_MONTHS)

    records: list[dict[str, object]] = []
    total = N_MONTHS * len(PRODUCT_CATALOG) * len(CHANNELS) * len(REGIONS)

    with tqdm(total=total, desc="Generating transactions") as pbar:
        for month_idx in range(N_MONTHS):
            m = macro.iloc[month_idx]

            for product in PRODUCT_CATALOG:
                for channel in CHANNELS:
                    for region in REGIONS:
                        # ── Resolve FX rate for this region ──
                        devise = str(region["devise_locale"])
                        if devise == "XOF":
                            taux = float(m["taux_usd_xof"])
                        elif devise == "XAF":
                            taux = float(m["taux_usd_xaf"])
                        else:
                            taux = float(m["taux_usd_mad"])

                        # ── Resolve inflation for this region ──
                        code = str(region["country_code"])
                        inflation = float(m[f"inflation_{code}"])

                        # ── COGS ──
                        cogs = _compute_cogs(
                            base_oil_usd_l=float(
                                product["base_oil_usd_l"]
                            ),
                            brent_usd=float(m["prix_brent_usd"]),
                            taux_usd_local=taux,
                            rng=rng,
                        )

                        # ── Pricing ──
                        pricing = _compute_pricing(
                            cogs_total=cogs["cogs_total"],
                            channel=channel,
                            rng=rng,
                        )

                        # ── Volume ──
                        volume = _compute_volume(
                            product=product,
                            channel=channel,
                            region=region,
                            month_idx=month_idx,
                            rng=rng,
                        )

                        # ── Competitor price ──
                        prix_conc = _compute_competitor_price(
                            nsp=pricing["nsp"],
                            channel=channel,
                            rng=rng,
                        )

                        # ── Margins ──
                        marge_brute = round(
                            pricing["nsp"] - cogs["cogs_total"], 2
                        )
                        marge_pct = (
                            round(marge_brute / pricing["nsp"], 4)
                            if pricing["nsp"] > 0
                            else 0.0
                        )

                        # ── Competitive index ──
                        indice = _compute_competitive_index(
                            nsp=pricing["nsp"],
                            prix_concurrent=prix_conc,
                            rng=rng,
                        )

                        records.append({
                            "date": m["date"],
                            "sku_id": product["sku_id"],
                            "produit": product["produit"],
                            "famille": product["famille"],
                            "canal": channel["canal"],
                            "region": region["region"],
                            "devise_locale": devise,
                            "cout_huile_base": cogs["cout_huile_base"],
                            "cout_additifs": cogs["cout_additifs"],
                            "cout_packaging": cogs["cout_packaging"],
                            "cout_transport": cogs["cout_transport"],
                            "cout_stockage": cogs["cout_stockage"],
                            "cogs_total": cogs["cogs_total"],
                            "prix_concurrent": prix_conc,
                            "prix_vente_brut": pricing["prix_vente_brut"],
                            "remise_pct": pricing["remise_pct"],
                            "nsp": pricing["nsp"],
                            "volume_vendu": volume,
                            "marge_brute": marge_brute,
                            "marge_brute_pct": marge_pct,
                            "inflation_locale": inflation,
                            "taux_usd_local": taux,
                            "prix_brent_usd": float(
                                m["prix_brent_usd"]
                            ),
                            "indice_conc": indice,
                        })
                        pbar.update(1)

    df = pd.DataFrame(records)
    assert df.shape[0] == EXPECTED_ROWS, (
        f"Expected {EXPECTED_ROWS:,} rows, got {df.shape[0]:,}"
    )
    logger.success(
        "Dataset generated: {:,} rows × {} columns", *df.shape
    )
    return df
