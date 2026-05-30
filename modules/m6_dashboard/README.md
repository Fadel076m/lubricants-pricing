# Module 6 — Executive Dashboard Plotly Dash

## Objectif
Dashboard multi-pages Plotly Dash déployé sur Render.com,
accessible par un recruteur via URL publique stable.

## Statut
Terminé ✅ — testé le 2026-05-29 (HTTP 200 confirmé)

## Usage
```bash
python -m modules.m6_dashboard.app
# ou
python -m modules.m6_dashboard.app --port 8051
```
URL : http://localhost:8050/

## Architecture Dash (multi-pages obligatoire)
```
modules/m6_dashboard/
├── app.py              # Point d'entrée Dash, layout principal, navbar
├── pages/
│   ├── executive.py    # Page 1 — Executive View
│   ├── pricing.py      # Page 2 — Pricing View + Simulateur PI
│   └── portfolio.py    # Page 3 — Portfolio View + Gap Analysis
└── components/
    ├── kpi_cards.py    # Composants KPI réutilisables
    ├── charts.py       # Graphiques Plotly réutilisables
    └── filters.py      # Filtres globaux (période, région, canal)
```

## Page 1 — Executive View
- KPIs globaux : CA total · Volume total · Marge brute moyenne · vs mois précédent
- Graphique évolution mensuelle CA + Marge (12 mois glissants)
- Répartition CA par région (bar chart)
- Top 5 SKUs rentables + Bottom 5 SKUs en alerte

## Page 2 — Pricing View
- Benchmark prix NSP vs concurrent par canal (barres groupées)
- Évolution NSP et COGS sur 36 mois (dual-axis line chart)
- **Simulateur PI interactif** : slider "Choc base oil +X%" → PI recommandé en temps réel
- Scénarios A/B/C : tableau comparatif impact CA/Marge/Volume
- Indice concurrence par région

## Page 3 — Portfolio View
- Matrice profitabilité SKU : scatter Volume vs Marge% (quadrants BCG)
- Waterfall COGS 5 postes par SKU sélectionné
- Gap Analysis : barres Gap Réel−Prévu par SKU/mois
- Tableau exportable Excel : SKU / Canal / Région / NSP / Marge / Forecast / Gap
- Alertes SKUs marge < 20% dans les 30 derniers jours

## Palette de couleurs (à utiliser dans tous les graphiques)
- Navy principal : #0D2B45
- Ambre accent : #BA7517
- Vert marge saine : #0F6E56
- Rouge alerte : #993C1D
- Gris neutre : #F4F4F2

## KPIs techniques cibles
- Latence callback simulateur PI < 400ms
- Disponibilité Render.com ≥ 99%
- Compatible mobile (responsive layout)

## Déploiement
1. `docker-compose.yml` : Dash + FastAPI + PostgreSQL Supabase
2. `Dockerfile` pour l'app Dash
3. GitHub Actions : test → build → deploy Render.com
4. UptimeRobot (gratuit) : ping toutes les 5 min pour éviter la mise en veille
