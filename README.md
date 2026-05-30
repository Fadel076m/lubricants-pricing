# AI-Powered Lubricants Portfolio & Pricing Management System

> Projet portfolio — Lubricants Portfolio & Pricing Manager | Afrique de l'Ouest

[![CI](https://github.com/Fadel076m/lubricants-pricing/actions/workflows/ci.yml/badge.svg)](https://github.com/Fadel076m/lubricants-pricing/actions)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-green)](https://lubricants-dash.onrender.com)
[![API](https://img.shields.io/badge/API-Live-blue)](https://lubricants-api.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.16-purple)](https://dash.plotly.com)

## Présentation

Plateforme complète d'analyse et d'optimisation du pricing lubrifiant couvrant les marchés
B2B et B2C en Afrique de l'Ouest (Dakar · Abidjan · Douala · Casablanca).

Le projet démontre la maîtrise de l'intégralité de la chaîne de valeur d'un Pricing Manager :
de la collecte de données marché jusqu'au déploiement d'un dashboard exécutif en production.

**Stack** : Python · Plotly Dash · FastAPI · Docker · Render.com · GitHub Actions

**Budget** : zéro — toutes données gratuites ou synthétiques (EIA API · Frankfurter · World Bank · Python Faker)

## Liens en production

| Service | URL |
|---------|-----|
| Dashboard exécutif | [lubricants-dash.onrender.com](https://lubricants-dash.onrender.com) |
| API REST (Swagger) | [lubricants-api.onrender.com/docs](https://lubricants-api.onrender.com/docs) |

> Les services Render.com gratuits se mettent en veille après 15 min d'inactivité — prévoir ~30s de cold start.

## Modules

| # | Module | Statut | Description |
|---|--------|--------|-------------|
| M1 | Market & Pricing Insights | Terminé ✅ | Benchmark concurrence · élasticité-prix · analyse FX |
| M2 | Margin Analysis | Terminé ✅ | Décomposition COGS 5 postes · alertes marge · sensibilité Brent |
| M3 | Pricing Simulation Engine | Terminé ✅ | PI calculator · scénarios A/B/C · Monte Carlo |
| M4 | Forecasting | Terminé ✅ | Prophet / XGBoost / LSTM · sélection automatique meilleur modèle |
| M5 | Gap Analysis | Terminé ✅ | Écart réel/prévu · root cause · rapport HTML automatique |
| M6 | Executive Dashboard Dash | Terminé ✅ | 3 pages : Executive · Pricing · Portfolio |
| M7 | FastAPI REST API | Terminé ✅ | 10 endpoints · filtres · Swagger · CORS sécurisé |
| M8 | Deploy Docker + Render | Terminé ✅ | 2 images slim · GitHub Actions CI · render.yaml Blueprint |

## Architecture

```
lubricants-pricing/
├── modules/
│   ├── m1_market_insights/     # Benchmark marché, élasticité
│   ├── m2_margin_analysis/     # COGS, marges, alertes
│   ├── m3_simulation_engine/   # PI calculator, scénarios
│   ├── m4_forecasting/         # Prophet, XGBoost, LSTM
│   ├── m5_gap_analysis/        # Gap réel/prévu, rapports
│   ├── m6_dashboard/           # Plotly Dash multi-pages
│   ├── m7_api/                 # FastAPI + Pydantic v2
│   └── shared/                 # Utilitaires partagés
├── data/
│   ├── processed/              # Parquets agrégés (versionnés)
│   └── synthetic/              # Dataset 14 400 lignes
├── tests/
│   ├── m2_margin_analysis/     # 21 tests unitaires
│   └── m3_simulation_engine/   # 21 tests unitaires
├── Dockerfile.api              # Image FastAPI (python:3.11-slim)
├── Dockerfile.dash             # Image Dash (python:3.11-slim)
└── render.yaml                 # Blueprint Render.com
```

## Dataset

- **Période** : Jan 2022 – Déc 2024 (36 mois)
- **SKUs** : 20 produits (Moteur · Hydraulique · Transmission · Marine · Graisse)
- **Canaux** : 5 (B2C GMS · B2C Réseau pétrolier · B2B Industrie · B2B OEM · Export)
- **Régions** : 4 (Dakar-SN · Abidjan-CI · Douala-CM · Casablanca-MA)
- **Volume total** : 14 400 lignes mensuelles

## API Endpoints

| Méthode | Path | Description |
|---------|------|-------------|
| GET | `/api/kpis` | KPIs filtrés (CA, Volume, Marge, NSP + deltas) |
| GET | `/api/products` | Liste produits avec tri |
| GET | `/api/products/{sku_id}` | Détail produit |
| GET | `/api/pricing/benchmark` | NSP vs concurrent par canal |
| GET | `/api/pricing/trend` | Tendance NSP/COGS mensuelle |
| GET | `/api/forecasts` | Prévisions 30/60/90 jours |
| GET | `/api/gap/sku` | Fiabilité prévisions par SKU |
| GET | `/api/gap/region` | Écart réel/prévu par région |
| POST | `/api/simulate/pi` | PI requis selon choc Brent |
| POST | `/api/simulate/scenarios` | Comparaison scénarios A/B/C |

Tous les endpoints acceptent les filtres `?region=&canal=&famille=&period=`.

## Installation locale

```bash
git clone https://github.com/Fadel076m/lubricants-pricing.git
cd lubricants-pricing
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env   # Remplir les clés API gratuites (EIA, Supabase)

# Lancer l'API
uvicorn modules.m7_api.main:app --reload --port 8000

# Lancer le Dashboard
python -m modules.m6_dashboard.app
```

## Tests

```bash
pytest tests/ --cov=modules/m2_margin_analysis --cov=modules/m3_simulation_engine -v
# 47 passed — couverture 52% sur modules core
```

## Résultats ML (données synthétiques)

| Cible | Modèle | MAPE | Cible |
|-------|--------|------|-------|
| volume_vendu | LSTM | 2.68% | < 8% ✅ |
| nsp | Prophet | 3.99% | < 5% ✅ |
| marge_brute_pct | XGBoost | 1.49% | — |

## Déploiement

Le projet se déploie via [render.yaml](render.yaml) en deux services Docker indépendants.
Voir [Dockerfile.api](Dockerfile.api) et [Dockerfile.dash](Dockerfile.dash).

```bash
# Docker local
docker build -f Dockerfile.api -t lubricants-api .
docker build -f Dockerfile.dash -t lubricants-dash .
```
