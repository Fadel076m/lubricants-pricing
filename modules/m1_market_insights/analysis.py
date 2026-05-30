"""
Market & Pricing Insights Analysis — Module 1

POURQUOI CE FICHIER ?
    Un Pricing Manager ne regarde pas que ses propres coûts. Il doit s'assurer 
    que son positionnement prix (NSP) est cohérent par rapport au marché (prix concurrent).
    Ce script produit les KPIs et agrégations nécessaires pour analyser notre 
    compétitivité (benchmark, élasticité, effet de change) et alimenter le dashboard.

OUTPUTS:
    data/processed/market_insights.parquet (données agrégées pour le Dash)
"""

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.linear_model import LinearRegression

def compute_price_evolution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule l'évolution mensuelle moyenne du prix de vente net (NSP) vs le prix concurrent.
    
    Args:
        df: DataFrame des transactions.
        
    Returns:
        DataFrame indexé par mois avec NSP et prix_concurrent moyens.
    """
    evolution = df.groupby('date')[['nsp', 'prix_concurrent']].mean().reset_index()
    evolution['ecart_pct'] = (evolution['nsp'] - evolution['prix_concurrent']) / evolution['prix_concurrent']
    return evolution


def compute_channel_benchmark(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le benchmark des prix par canal.
    
    Args:
        df: DataFrame des transactions.
        
    Returns:
        DataFrame agrégé par canal avec indice concurrentiel et écart moyen.
    """
    bench = df.groupby('canal').agg(
        nsp_moyen=('nsp', 'mean'),
        prix_conc_moyen=('prix_concurrent', 'mean'),
        indice_conc_moyen=('indice_conc', 'mean')
    ).reset_index()
    
    bench['ecart_absolu'] = bench['nsp_moyen'] - bench['prix_conc_moyen']
    bench['ecart_pct'] = bench['ecart_absolu'] / bench['prix_conc_moyen']
    
    return bench


def compute_regional_positioning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le positionnement prix par région pour la heatmap.
    
    Args:
        df: DataFrame des transactions.
        
    Returns:
        DataFrame croisant Région et Famille avec l'écart prix en pourcentage.
    """
    pivot = df.pivot_table(
        index='region', 
        columns='famille', 
        values='nsp', 
        aggfunc='mean'
    )
    
    pivot_conc = df.pivot_table(
        index='region', 
        columns='famille', 
        values='prix_concurrent', 
        aggfunc='mean'
    )
    
    # Ecart en % vs concurrence par région et famille
    positioning = (pivot - pivot_conc) / pivot_conc
    return positioning


def compute_price_elasticity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule l'élasticité-prix historique (modèle log-log) par canal.
    Formule: log(Volume) = alpha + beta * log(Prix) + epsilon, où beta = élasticité.
    
    Args:
        df: DataFrame des transactions.
        
    Returns:
        DataFrame contenant le coefficient d'élasticité par canal.
    """
    results = []
    
    for canal in df['canal'].unique():
        canal_df = df[df['canal'] == canal].copy()
        
        # Filtre de précaution
        canal_df = canal_df[(canal_df['nsp'] > 0) & (canal_df['volume_vendu'] > 0)]
        
        if len(canal_df) < 10:
            continue
            
        X = np.log(canal_df['nsp']).values.reshape(-1, 1)
        y = np.log(canal_df['volume_vendu']).values
        
        model = LinearRegression()
        model.fit(X, y)
        elasticity = model.coef_[0]
        
        results.append({
            'canal': canal,
            'elasticite': round(elasticity, 2)
        })
        
    return pd.DataFrame(results).sort_values('elasticite')


def compute_brent_cogs_correlation(df: pd.DataFrame) -> float:
    """
    Calcule la corrélation R² entre le Brent (USD) et le COGS base oil en monnaie locale.
    
    Args:
        df: DataFrame des transactions.
        
    Returns:
        Coefficient R² (float).
    """
    # On agrège par mois pour gommer l'effet SKU
    monthly = df.groupby('date')[['prix_brent_usd', 'cout_huile_base']].mean()
    
    X = monthly['prix_brent_usd'].values.reshape(-1, 1)
    y = monthly['cout_huile_base'].values
    
    model = LinearRegression()
    model.fit(X, y)
    r2 = model.score(X, y)
    
    return round(r2, 4)


def run_all_analyses(input_path: str, output_path: str) -> None:
    """
    Exécute toutes les analyses M1 et sauvegarde les résultats.
    """
    logger.info(f"Chargement des données depuis {input_path}")
    df = pd.read_parquet(input_path)
    
    # 1. Évolution
    evolution_df = compute_price_evolution(df)
    
    # 2. Benchmark Canal
    channel_df = compute_channel_benchmark(df)
    
    # 3. Positionnement Régional
    region_df = compute_regional_positioning(df)
    
    # 4. Élasticité
    elasticity_df = compute_price_elasticity(df)
    
    # 5. Corrélation Brent
    r2_brent = compute_brent_cogs_correlation(df)
    logger.info(f"Corrélation R² Brent vs COGS Base Oil: {r2_brent}")
    
    # Création du dossier processed si non existant
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # On sauvegarde un dictionnaire d'analyses sous format parquet en utilisant pandas concat
    # Pour un stockage simple, on pourrait stocker plusieurs tables ou utiliser un dictionnaire
    # Vu qu'on veut alimenter le dashboard, stocker l'évolution globale suffit souvent pour le parquet principal M1.
    # On va enregistrer l'évolution et sauvegarder le reste dans des fichiers séparés ou logger les insights.
    
    evolution_df.to_parquet(output_path, index=False)
    
    # Export des benchmarks additionnels pour le Dash
    channel_df.to_parquet(output_path.replace('.parquet', '_channel.parquet'), index=False)
    
    # Heatmap nécessite le reset index
    region_df.reset_index().to_parquet(output_path.replace('.parquet', '_region.parquet'), index=False)
    
    elasticity_df.to_parquet(output_path.replace('.parquet', '_elasticity.parquet'), index=False)
    
    logger.success(f"Analyses M1 sauvegardées dans {os.path.dirname(output_path)}")


if __name__ == "__main__":
    INPUT_FILE = "data/synthetic/transactions.parquet"
    OUTPUT_FILE = "data/processed/market_insights.parquet"
    run_all_analyses(INPUT_FILE, OUTPUT_FILE)
