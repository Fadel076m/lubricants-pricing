# Module 2 — Margin Analysis

## Objectif
Calculer et analyser les marges brutes et nettes par SKU, canal et région.
Identifier les SKUs sous seuil critique et les drivers de rentabilité.

## Statut
Non démarré

## Fichiers à créer
- [ ] `cogs_engine.py` — moteur de calcul COGS 5 postes
- [ ] `margin_calculator.py` — marge brute/nette par SKU/canal/région
- [ ] `alerts.py` — détection SKUs sous seuil critique
- [ ] `visualizations.py` — waterfall chart, heatmap marge

## Formule centrale
```
Marge brute (%) = (NSP - COGS) / NSP
COGS = cout_huile_base + cout_additifs + cout_packaging + cout_transport + cout_stockage
```

## COGS — 5 postes (spécifique Afrique Ouest)
| Poste | Part COGS typique | Note |
|-------|------------------|------|
| Base oil (Group II/III) | 58–72% | Corrélé ICIS / proxy WTI |
| Additifs (DI package, VM) | 20–28% | Ratio fixe par formule |
| Packaging (bidon, fût) | 5–7% | Variable selon conditionnement |
| Transport | 7–9% | ÉLEVÉ Afrique Ouest vs Europe |
| Stockage | 4–5% | Température contrôlée |

## Inputs
- `data/synthetic/transactions.parquet`

## Outputs
- `data/processed/margins_by_sku.parquet`
- `data/processed/cogs_breakdown.parquet`
- `data/processed/sku_alerts.parquet`

## KPIs du module
- Marge brute moyenne par famille produit
- Marge brute moyenne par canal
- Marge brute par région
- Nombre de SKUs sous seuil critique (< 20%)
- Part du COGS base oil dans le COGS total (%)

## Seuils d'alerte
- Marge brute ≥ 30% → Vert (saine)
- Marge brute 20–29% → Ambre (surveillance)
- Marge brute < 20% → Rouge (action PI requise)

## Tests unitaires obligatoires
- test_cogs_calculation : vérifier que la somme des 5 postes = cogs_total
- test_margin_formula : vérifier (NSP - COGS) / NSP
- test_alert_thresholds : vérifier les seuils 20% et 30%
