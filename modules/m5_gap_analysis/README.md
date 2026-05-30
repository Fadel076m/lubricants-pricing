# Module 5 — Gap Analysis

## Objectif
Comparer les prévisions vs les valeurs réelles pour identifier
les écarts de performance et générer des rapports automatiques.

## Statut
Terminé ✅ — testé le 2026-05-29 (3.6s)

## Fichiers créés
- [x] `gap_engine.py` — calcul Gap = Réel − Prévu par dimension
- [x] `root_cause.py` — identification des causes d'écart
- [x] `report_generator.py` — rapport HTML (+ PDF WeasyPrint si installé)
- [x] `alerts.py` — alertes dépassement seuil gap
- [x] `visualizations.py` — 5 figures Plotly (global, waterfall, mensuel, heatmap)
- [x] `__init__.py` — package exports
- [x] `run_m5.py` — pipeline runner CLI

## Usage
```bash
python -m modules.m5_gap_analysis.run_m5
python -m modules.m5_gap_analysis.run_m5 --month 2025-01
```

## Formule centrale
```
Gap absolu  = Valeur réelle - Valeur prévue
Gap relatif = (Valeur réelle - Valeur prévue) / Valeur prévue × 100
```

## Dimensions d'analyse
- Gap par SKU (quels produits sous/sur-performent ?)
- Gap par canal (quel canal dévie du plan ?)
- Gap par région (quelle géographie surprend ?)
- Gap par mois (quelles périodes posent problème ?)

## Seuils d'alerte
- Gap > +5% → Favorable (vert)
- Gap entre −5% et +5% → Dans la cible (bleu)
- Gap < −5% → Défavorable (orange)
- Gap < −10% → Critique (rouge)

## Inputs
- `data/processed/forecasts_30_60_90.parquet`
- `data/synthetic/transactions.parquet` (valeurs réelles)

## Outputs
- `data/processed/gap_analysis.parquet`
- `reports/gap_report_YYYY_MM.pdf` (généré automatiquement)

## Rapport PDF (WeasyPrint)
Contenu du rapport mensuel automatique :
1. Résumé exécutif : gap global CA / Volume / Marge
2. Top 5 SKUs avec plus grand écart défavorable
3. Analyse par canal et région
4. Recommandations automatiques
