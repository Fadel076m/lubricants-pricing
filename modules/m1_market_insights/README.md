# Module 1 — Market & Pricing Insights

## Objectif
Analyser le marché lubrifiant et le positionnement concurrentiel
par canal et par région (Dakar, Abidjan, Douala, Casablanca).

## Statut
Non démarré

## Fichiers à créer
- [ ] `data_collection.py` — collecte APIs gratuites + scraping prix concurrents
- [ ] `analysis.py` — benchmark prix, corrélation prix-volume, sensibilité
- [ ] `visualizations.py` — graphiques Plotly pour le dashboard

## Inputs
- Dataset synthétique : `data/synthetic/transactions.parquet`
- EIA API : prix Brent hebdomadaire
- Frankfurter API : taux USD/XOF
- Scraping : prix catalogue publics concurrents

## Outputs
- `data/processed/market_insights.parquet`
- `data/processed/competitor_prices.parquet`

## KPIs du module
- Prix moyen marché par canal et région
- Écart prix NSP vs concurrent (en % et en valeur absolue)
- Indice de pression concurrentielle (0 à 1)
- Corrélation prix Brent vs COGS base oil (R²)

## Analyses à produire
1. Évolution mensuelle prix concurrents vs NSP sur 36 mois
2. Benchmark prix par canal : B2C GMS vs B2C Réseau vs B2B
3. Heatmap régionale : positionnement prix (premium / parité / discount)
4. Analyse de sensibilité : élasticité-prix observée par segment
5. Corrélation prix Brent USD → COGS base oil en XOF (effet taux change inclus)

## Connexion avec autres modules
- Fournit `indice_conc` au Module 3 (simulateur PI)
- Fournit `prix_brent_usd` et `taux_usd_local` au Module 4 (forecasting)
