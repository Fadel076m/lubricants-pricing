"""Validation and summary checks for the generated dataset."""
import pandas as pd
import numpy as np
from loguru import logger
from .config import EXPECTED_ROWS, N_MONTHS

def validate_dataset(df: pd.DataFrame) -> None:
    """Run quality checks on the generated dataset.

    Validates shape, completeness, column schema, cardinalities,
    and all calculated field formulas (COGS sum, NSP, margin).

    Args:
        df: The generated transactions DataFrame.

    Raises:
        AssertionError: If any validation check fails.
    """
    checks_passed = 0

    # ── Shape ──
    assert df.shape[0] == EXPECTED_ROWS, f"Row count: {df.shape[0]}"
    assert df.shape[1] == 24, f"Column count: {df.shape[1]}"
    checks_passed += 2

    # ── No missing values ──
    nulls = df.isnull().sum().sum()
    assert nulls == 0, f"Found {nulls} null values"
    checks_passed += 1

    # ── Column names match spec exactly ──
    expected_cols = [
        "date", "sku_id", "produit", "famille", "canal", "region",
        "devise_locale", "cout_huile_base", "cout_additifs",
        "cout_packaging", "cout_transport", "cout_stockage",
        "cogs_total", "prix_concurrent", "prix_vente_brut",
        "remise_pct", "nsp", "volume_vendu", "marge_brute",
        "marge_brute_pct", "inflation_locale", "taux_usd_local",
        "prix_brent_usd", "indice_conc",
    ]
    assert list(df.columns) == expected_cols, (
        f"Column mismatch: {set(df.columns) ^ set(expected_cols)}"
    )
    checks_passed += 1

    # ── Cardinalities ──
    assert df["sku_id"].nunique() == 20, "SKU count mismatch"
    assert df["canal"].nunique() == 5, "Channel count mismatch"
    assert df["region"].nunique() == 4, "Region count mismatch"
    assert df["date"].nunique() == N_MONTHS, "Month count mismatch"
    checks_passed += 4

    # ── COGS = sum of 5 components ──
    cogs_check = (
        df["cout_huile_base"]
        + df["cout_additifs"]
        + df["cout_packaging"]
        + df["cout_transport"]
        + df["cout_stockage"]
    )
    assert np.allclose(cogs_check, df["cogs_total"], atol=0.05), (
        "COGS components do not sum to cogs_total"
    )
    checks_passed += 1

    # ── NSP = prix_vente_brut × (1 − remise_pct) ──
    nsp_check = df["prix_vente_brut"] * (1 - df["remise_pct"])
    assert np.allclose(nsp_check, df["nsp"], atol=0.02), (
        "NSP formula mismatch"
    )
    checks_passed += 1

    # ── Marge brute = NSP − COGS ──
    margin_check = df["nsp"] - df["cogs_total"]
    assert np.allclose(margin_check, df["marge_brute"], atol=0.02), (
        "Margin formula mismatch"
    )
    checks_passed += 1

    # ── Value ranges ──
    assert (df["volume_vendu"] >= 10).all(), "Volume below minimum"
    assert df["remise_pct"].between(0, 1).all(), "Discount out of range"
    assert df["indice_conc"].between(0, 1).all(), "Index out of range"
    assert (df["prix_brent_usd"] > 0).all(), "Negative Brent"
    assert (df["taux_usd_local"] > 0).all(), "Negative FX rate"
    checks_passed += 5

    logger.success("All {} validation checks passed ✅", checks_passed)


def print_summary(df: pd.DataFrame) -> None:
    """Print a human-readable summary of the generated dataset.

    Args:
        df: The generated transactions DataFrame.
    """
    xof_mask = df["devise_locale"] == "XOF"
    mad_mask = df["devise_locale"] == "MAD"

    alert_count = (df["marge_brute_pct"] < 0.20).sum()
    amber_count = (
        (df["marge_brute_pct"] >= 0.20)
        & (df["marge_brute_pct"] < 0.30)
    ).sum()
    green_count = len(df) - alert_count - amber_count

    print("\n" + "=" * 62)
    print("  DATASET SUMMARY — Lubricants Pricing")
    print("=" * 62)
    print(f"  Rows             : {df.shape[0]:>10,}")
    print(f"  Columns          : {df.shape[1]:>10}")
    print(f"  Period           : {df['date'].min()} -> {df['date'].max()}")
    print(f"  SKUs             : {df['sku_id'].nunique():>10}")
    print(f"  Channels         : {df['canal'].nunique():>10}")
    print(f"  Regions          : {df['region'].nunique():>10}")
    print("-" * 62)
    print(f"  Avg margin %     : {df['marge_brute_pct'].mean():>10.1%}")
    print(f"  Median margin %  : {df['marge_brute_pct'].median():>10.1%}")
    print(f"  Min margin %     : {df['marge_brute_pct'].min():>10.1%}")
    print(f"  Max margin %     : {df['marge_brute_pct'].max():>10.1%}")
    print("-" * 62)
    alert_pct = alert_count / len(df)
    amber_pct = amber_count / len(df)
    green_pct = green_count / len(df)
    print(
        f"  !! Margin < 20%  : {alert_count:>6,} records ({alert_pct:.1%})"
    )
    print(
        f"  !! Margin 20-30% : {amber_count:>6,} records ({amber_pct:.1%})"
    )
    print(
        f"  OK Margin >= 30% : {green_count:>6,} records ({green_pct:.1%})"
    )
    print("-" * 62)
    if xof_mask.any():
        avg_cogs_xof = df.loc[xof_mask, "cogs_total"].mean()
        avg_nsp_xof = df.loc[xof_mask, "nsp"].mean()
        print(f"  Avg COGS (XOF)   : {avg_cogs_xof:>10,.0f} XOF/L")
        print(f"  Avg NSP  (XOF)   : {avg_nsp_xof:>10,.0f} XOF/L")
    if mad_mask.any():
        avg_cogs_mad = df.loc[mad_mask, "cogs_total"].mean()
        avg_nsp_mad = df.loc[mad_mask, "nsp"].mean()
        print(f"  Avg COGS (MAD)   : {avg_cogs_mad:>10,.0f} MAD/L")
        print(f"  Avg NSP  (MAD)   : {avg_nsp_mad:>10,.0f} MAD/L")
    print("-" * 62)
    brent_min = df["prix_brent_usd"].min()
    brent_max = df["prix_brent_usd"].max()
    print(f"  Brent range      : ${brent_min:.1f} – ${brent_max:.1f}")
    if xof_mask.any():
        xof_min = df.loc[xof_mask, "taux_usd_local"].min()
        xof_max = df.loc[xof_mask, "taux_usd_local"].max()
        print(f"  USD/XOF range    : {xof_min:.1f} – {xof_max:.1f}")
    print("=" * 62 + "\n")

    # ── Margin distribution by channel ──
    print("  MARGIN % BY CHANNEL:")
    print("  " + "-" * 50)
    for canal in df["canal"].unique():
        mask = df["canal"] == canal
        avg = df.loc[mask, "marge_brute_pct"].mean()
        print(f"    {canal:<18s} : {avg:.1%}")
    print()
