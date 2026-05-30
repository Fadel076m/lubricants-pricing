"""Static catalogs for products, regions, and channels."""
from typing import Final

PRODUCT_CATALOG: Final[list[dict[str, object]]] = [
    # ── Moteur (8 SKUs) — core business, 40% of SKU count ────────────────
    {
        "sku_id": "SKU-5W30-SYN-1L",
        "produit": "Huile moteur 5W30 Full Synthetic 1L",
        "famille": "Moteur",
        "base_oil_usd_l": 1.05,
        "additive_ratio": 0.35,
        "pkg_usd_l": 0.12,
        "volume_base": 800,
    },
    {
        "sku_id": "SKU-5W30-SYN-5L",
        "produit": "Huile moteur 5W30 Full Synthetic 5L",
        "famille": "Moteur",
        "base_oil_usd_l": 1.05,
        "additive_ratio": 0.35,
        "pkg_usd_l": 0.07,
        "volume_base": 1200,
    },
    {
        "sku_id": "SKU-5W40-SYN-1L",
        "produit": "Huile moteur 5W40 Full Synthetic 1L",
        "famille": "Moteur",
        "base_oil_usd_l": 1.00,
        "additive_ratio": 0.33,
        "pkg_usd_l": 0.12,
        "volume_base": 700,
    },
    {
        "sku_id": "SKU-10W40-SEMI-1L",
        "produit": "Huile moteur 10W40 Semi-Synthetic 1L",
        "famille": "Moteur",
        "base_oil_usd_l": 0.80,
        "additive_ratio": 0.30,
        "pkg_usd_l": 0.12,
        "volume_base": 1500,
    },
    {
        "sku_id": "SKU-10W40-SEMI-5L",
        "produit": "Huile moteur 10W40 Semi-Synthetic 5L",
        "famille": "Moteur",
        "base_oil_usd_l": 0.80,
        "additive_ratio": 0.30,
        "pkg_usd_l": 0.07,
        "volume_base": 2000,
    },
    {
        "sku_id": "SKU-15W40-MIN-1L",
        "produit": "Huile moteur 15W40 Minerale 1L",
        "famille": "Moteur",
        "base_oil_usd_l": 0.58,
        "additive_ratio": 0.28,
        "pkg_usd_l": 0.12,
        "volume_base": 3500,
    },
    {
        "sku_id": "SKU-15W40-MIN-5L",
        "produit": "Huile moteur 15W40 Minerale 5L",
        "famille": "Moteur",
        "base_oil_usd_l": 0.58,
        "additive_ratio": 0.28,
        "pkg_usd_l": 0.07,
        "volume_base": 4000,
    },
    {
        "sku_id": "SKU-20W50-MIN-1L",
        "produit": "Huile moteur 20W50 Minerale 1L",
        "famille": "Moteur",
        "base_oil_usd_l": 0.52,
        "additive_ratio": 0.25,
        "pkg_usd_l": 0.12,
        "volume_base": 5000,
    },
    # ── Hydraulique (4 SKUs) — B2B industrial, high volumes ──────────────
    {
        "sku_id": "SKU-HYD-ISO32-20L",
        "produit": "Huile hydraulique ISO 32 20L",
        "famille": "Hydraulique",
        "base_oil_usd_l": 0.55,
        "additive_ratio": 0.22,
        "pkg_usd_l": 0.04,
        "volume_base": 3000,
    },
    {
        "sku_id": "SKU-HYD-ISO46-20L",
        "produit": "Huile hydraulique ISO 46 20L",
        "famille": "Hydraulique",
        "base_oil_usd_l": 0.58,
        "additive_ratio": 0.24,
        "pkg_usd_l": 0.04,
        "volume_base": 4500,
    },
    {
        "sku_id": "SKU-HYD-ISO68-20L",
        "produit": "Huile hydraulique ISO 68 20L",
        "famille": "Hydraulique",
        "base_oil_usd_l": 0.60,
        "additive_ratio": 0.24,
        "pkg_usd_l": 0.04,
        "volume_base": 2500,
    },
    {
        "sku_id": "SKU-HYD-ISO46-200L",
        "produit": "Huile hydraulique ISO 46 Fut 200L",
        "famille": "Hydraulique",
        "base_oil_usd_l": 0.58,
        "additive_ratio": 0.24,
        "pkg_usd_l": 0.02,
        "volume_base": 8000,
    },
    # ── Transmission (3 SKUs) — ATF and gear oils ────────────────────────
    {
        "sku_id": "SKU-ATF-DIII-1L",
        "produit": "Fluide transmission ATF Dexron III 1L",
        "famille": "Transmission",
        "base_oil_usd_l": 0.85,
        "additive_ratio": 0.32,
        "pkg_usd_l": 0.12,
        "volume_base": 1800,
    },
    {
        "sku_id": "SKU-GEAR-80W90-1L",
        "produit": "Huile boite 80W90 GL-5 1L",
        "famille": "Transmission",
        "base_oil_usd_l": 0.65,
        "additive_ratio": 0.28,
        "pkg_usd_l": 0.12,
        "volume_base": 2200,
    },
    {
        "sku_id": "SKU-GEAR-75W90-SYN",
        "produit": "Huile boite 75W90 Synthetic GL-5 1L",
        "famille": "Transmission",
        "base_oil_usd_l": 0.95,
        "additive_ratio": 0.34,
        "pkg_usd_l": 0.12,
        "volume_base": 600,
    },
    # ── Marine (3 SKUs) — bulk drums for maritime & fishing ──────────────
    {
        "sku_id": "SKU-MAR-15W40-20L",
        "produit": "Huile marine 15W40 20L",
        "famille": "Marine",
        "base_oil_usd_l": 0.55,
        "additive_ratio": 0.25,
        "pkg_usd_l": 0.04,
        "volume_base": 2000,
    },
    {
        "sku_id": "SKU-MAR-30-200L",
        "produit": "Huile marine SAE 30 Fut 200L",
        "famille": "Marine",
        "base_oil_usd_l": 0.48,
        "additive_ratio": 0.22,
        "pkg_usd_l": 0.02,
        "volume_base": 6000,
    },
    {
        "sku_id": "SKU-MAR-40-200L",
        "produit": "Huile marine SAE 40 Fut 200L",
        "famille": "Marine",
        "base_oil_usd_l": 0.50,
        "additive_ratio": 0.22,
        "pkg_usd_l": 0.02,
        "volume_base": 5000,
    },
    # ── Graisse (2 SKUs) — industrial & automotive lubrication ───────────
    {
        "sku_id": "SKU-GRS-MP2-400G",
        "produit": "Graisse multi-usage MP2 400g",
        "famille": "Graisse",
        "base_oil_usd_l": 0.70,
        "additive_ratio": 0.30,
        "pkg_usd_l": 0.15,
        "volume_base": 900,
    },
    {
        "sku_id": "SKU-GRS-EP2-18KG",
        "produit": "Graisse EP2 Lithium Seau 18kg",
        "famille": "Graisse",
        "base_oil_usd_l": 0.65,
        "additive_ratio": 0.28,
        "pkg_usd_l": 0.03,
        "volume_base": 3000,
    },
]

assert len(PRODUCT_CATALOG) == 20, "Catalog must have exactly 20 SKUs"


# ══════════════════════════════════════════════════════════════════════════════
# REGIONS — 4 markets with different currencies and cost profiles
# ══════════════════════════════════════════════════════════════════════════════
# volume_factor : relative market size (1.0 = baseline Dakar)

REGIONS: Final[list[dict[str, object]]] = [
    {
        "region": "Dakar-SN",
        "devise_locale": "XOF",
        "country_code": "SN",
        "volume_factor": 1.00,
    },
    {
        "region": "Abidjan-CI",
        "devise_locale": "XOF",
        "country_code": "CI",
        "volume_factor": 1.15,
    },
    {
        "region": "Douala-CM",
        "devise_locale": "XAF",
        "country_code": "CM",
        "volume_factor": 0.85,
    },
    {
        "region": "Casablanca-MA",
        "devise_locale": "MAD",
        "country_code": "MA",
        "volume_factor": 1.30,
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# CHANNELS — 5 distribution channels with different economics
# ══════════════════════════════════════════════════════════════════════════════
# markup        : gross price multiplier vs COGS (before discount)
# remise_min/max: discount range specific to channel power dynamics
# volume_factor : volume multiplier vs product base volume
# price_spread  : std-dev of competitor price offset (channel competition)

CHANNELS: Final[list[dict[str, object]]] = [
    {
        "canal": "B2C GMS",
        "markup": 1.65,
        "remise_min": 0.03,
        "remise_max": 0.08,
        "volume_factor": 0.60,
        "price_spread": 0.04,
    },
    {
        "canal": "B2C Réseau",
        "markup": 1.60,
        "remise_min": 0.05,
        "remise_max": 0.12,
        "volume_factor": 0.80,
        "price_spread": 0.05,
    },
    {
        "canal": "B2B Industrie",
        "markup": 1.50,
        "remise_min": 0.10,
        "remise_max": 0.18,
        "volume_factor": 1.40,
        "price_spread": 0.06,
    },
    {
        "canal": "B2B OEM",
        "markup": 1.45,
        "remise_min": 0.15,
        "remise_max": 0.25,
        "volume_factor": 2.00,
        "price_spread": 0.08,
    },
    {
        "canal": "Export",
        "markup": 1.48,
        "remise_min": 0.08,
        "remise_max": 0.15,
        "volume_factor": 1.00,
        "price_spread": 0.07,
    },
]
