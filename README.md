# AI-Powered Lubricants Portfolio & Pricing Management System

> Projet portfolio personnel — Lubricants Pricing Manager | Afrique de l'Ouest

[![CI](https://github.com/USERNAME/lubricants-pricing/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/lubricants-pricing/actions)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-green)](https://lubricants-pricing.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.16-purple)](https://dash.plotly.com)

## Présentation

Plateforme d'analyse et d'optimisation du pricing lubrifiant couvrant :
les marchés B2B et B2C en Afrique de l'Ouest (Dakar, Abidjan, Douala, Casablanca),
6 modules analytiques indépendants, un dashboard Plotly Dash 3 pages,
et une API FastAPI documentée.

**Stack** : Python · Plotly Dash · FastAPI · Supabase · Docker · Render.com

**Budget** : zéro — toutes données gratuites ou synthétiques

## Modules

| # | Module | Statut |
|---|--------|--------|
| 1 | Market & Pricing Insights | Non démarré |
| 2 | Margin Analysis | Non démarré |
| 3 | Pricing Simulation Engine | Non démarré |
| 4 | Forecasting (Prophet / XGBoost / LSTM) | Non démarré |
| 5 | Gap Analysis | Non démarré |
| 6 | Executive Dashboard Plotly Dash | Non démarré |

## Installation rapide

```bash
git clone https://github.com/USERNAME/lubricants-pricing.git
cd lubricants-pricing
cp .env.example .env   # Remplir les clés API gratuites
pip install -r requirements.txt
python modules/m1_market_insights/data_collection.py
```

## Structure

Voir `ANTIGRAVITY_PROMPT.md` pour la documentation complète de l'architecture.

## Lien dashboard

[lubricants-pricing.onrender.com](https://lubricants-pricing.onrender.com) *(disponible après déploiement)*
