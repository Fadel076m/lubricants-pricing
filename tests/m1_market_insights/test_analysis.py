import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from modules.m1_market_insights.analysis import (
    compute_price_evolution,
    compute_channel_benchmark,
    compute_regional_positioning,
    compute_price_elasticity,
    compute_brent_cogs_correlation
)

@pytest.fixture
def sample_data():
    """
    Crée un mini DataFrame factice pour tester les fonctions d'analyse basiques.
    """
    data = {
        'date': ['2023-01', '2023-01', '2023-02', '2023-02', '2023-03', '2023-03'],
        'sku_id': ['SKU1', 'SKU2', 'SKU1', 'SKU2', 'SKU1', 'SKU2'],
        'produit': ['P1', 'P2', 'P1', 'P2', 'P1', 'P2'],
        'famille': ['Moteur', 'Transmission', 'Moteur', 'Transmission', 'Moteur', 'Transmission'],
        'canal': ['B2C GMS', 'B2B Industrie', 'B2C GMS', 'B2B Industrie', 'B2C GMS', 'B2B Industrie'],
        'region': ['Dakar-SN', 'Abidjan-CI', 'Dakar-SN', 'Abidjan-CI', 'Dakar-SN', 'Abidjan-CI'],
        'nsp': [1000, 1500, 950, 1450, 900, 1400],
        'prix_concurrent': [1050, 1500, 1000, 1400, 950, 1350],
        'volume_vendu': [500, 200, 550, 210, 600, 220],
        'indice_conc': [0.45, 0.50, 0.40, 0.55, 0.35, 0.60],
        'prix_brent_usd': [80.0, 80.0, 85.0, 85.0, 90.0, 90.0],
        'cout_huile_base': [600, 900, 620, 920, 650, 950]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_elasticity_data():
    """
    Crée au moins 10 lignes pour B2C GMS afin de passer le seuil de calcul d'élasticité.
    """
    n = 12
    data = {
        'date': [f'2023-{str(i%12 + 1).zfill(2)}' for i in range(n)],
        'sku_id': ['SKU1'] * n,
        'produit': ['P1'] * n,
        'famille': ['Moteur'] * n,
        'canal': ['B2C GMS'] * n,
        'region': ['Dakar-SN'] * n,
        'nsp': [1000 - i*10 for i in range(n)],
        'prix_concurrent': [1050 - i*10 for i in range(n)],
        'volume_vendu': [500 + i*50 for i in range(n)],
        'indice_conc': [0.45] * n,
        'prix_brent_usd': [80.0 + i for i in range(n)],
        'cout_huile_base': [600 + i*10 for i in range(n)]
    }
    return pd.DataFrame(data)

def test_compute_price_evolution(sample_data):
    evo_df = compute_price_evolution(sample_data)
    assert 'date' in evo_df.columns
    assert 'nsp' in evo_df.columns
    assert 'prix_concurrent' in evo_df.columns
    assert 'ecart_pct' in evo_df.columns
    
    assert len(evo_df) == 3
    assert abs(evo_df.iloc[0]['nsp'] - 1250) < 0.01

def test_compute_channel_benchmark(sample_data):
    bench_df = compute_channel_benchmark(sample_data)
    assert 'canal' in bench_df.columns
    assert 'ecart_pct' in bench_df.columns
    assert len(bench_df) == 2
    
    b2c_row = bench_df[bench_df['canal'] == 'B2C GMS']
    assert b2c_row['nsp_moyen'].iloc[0] == 950

def test_compute_regional_positioning(sample_data):
    region_df = compute_regional_positioning(sample_data)
    assert 'Moteur' in region_df.columns
    assert region_df.loc['Dakar-SN', 'Moteur'] == pytest.approx(-0.05, 0.01)

def test_compute_price_elasticity(sample_elasticity_data):
    elasticity_df = compute_price_elasticity(sample_elasticity_data)
    assert 'canal' in elasticity_df.columns
    assert 'elasticite' in elasticity_df.columns
    assert len(elasticity_df) == 1
    assert elasticity_df['elasticite'].iloc[0] < 0

def test_compute_brent_cogs_correlation(sample_data):
    r2 = compute_brent_cogs_correlation(sample_data)
    assert r2 >= 0.90
