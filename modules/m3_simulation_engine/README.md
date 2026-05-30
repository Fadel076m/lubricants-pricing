# Module 3 — Pricing Simulation Engine

## Objectif
Simuler l'impact d'un choc COGS sur les marges et recommander
automatiquement le price increase (PI) minimum par SKU et canal.

## Statut
Non démarré

## Fichiers à créer
- [ ] `pi_calculator.py` — calcul PI requis par choc base oil
- [ ] `elasticity_model.py` — modèle élasticité-prix OLS log-log par canal
- [ ] `scenario_engine.py` — simulation Monte Carlo scénarios A/B/C
- [ ] `visualizations.py` — graphiques Plotly avec sliders Dash

## Formule PI
```
PI_requis = (delta_COGS × ratio_COGS_NSP) / (1 - marge_cible)
```

## Élasticités-prix par canal (à calibrer sur données)
| Canal | Élasticité attendue | Interprétation |
|-------|--------------------|-|
| B2C GMS | ~ −1.4 | Très sensible au prix |
| B2C Réseau | ~ −1.1 | Sensible |
| B2B Industrie | ~ −0.6 | Modéré |
| B2B OEM | ~ −0.3 | Peu sensible (contrats) |
| Export | ~ −0.8 | Variable |

## Scénarios à simuler
- **Scénario A** : PI +3% → impact volume, marge, profit
- **Scénario B** : PI +5% → impact volume, marge, profit
- **Scénario C** : Prix inchangé → impact marge uniquement

## Inputs
- `data/processed/margins_by_sku.parquet`
- `data/processed/market_insights.parquet`
- Paramètre utilisateur : % de choc base oil (slider Dash)

## Outputs
- `data/processed/pi_recommendations.parquet`
- `data/processed/scenario_results.parquet`

## KPIs du module
- Précision recommandation PI : marge maintenue dans ±1pt (cible ≥ 85%)
- Latence calcul simulation : < 2 secondes
