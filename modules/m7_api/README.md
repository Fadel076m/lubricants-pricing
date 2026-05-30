# M7 — API REST FastAPI

API REST complète pour le système de gestion des prix et du portefeuille lubrifiants.

## Endpoints (10 routes)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Info API + liste des endpoints |
| GET | `/api/kpis` | KPIs filtrés (CA, Volume, Marge, NSP + deltas) |
| GET | `/api/products` | Liste produits (sort_by, limit, ordre) |
| GET | `/api/products/{sku_id}` | Détail d'un produit |
| GET | `/api/pricing/benchmark` | NSP moyen vs concurrent par canal |
| GET | `/api/pricing/trend` | Tendance mensuelle NSP / COGS |
| GET | `/api/forecasts` | Prévisions 30/60/90 jours (target, horizon) |
| GET | `/api/gap/sku` | Fiabilité des prévisions par SKU (hit-rate %) |
| GET | `/api/gap/region` | Écart moyen réel/prévu par région |
| POST | `/api/simulate/pi` | PI requis par SKU selon choc Brent |
| POST | `/api/simulate/scenarios` | Comparaison 3 scénarios de prix (élasticité −0.5) |

## Paramètres de filtre communs (GET)

| Param | Valeurs | Défaut |
|-------|---------|--------|
| `period` | `all`, `2024`, `2023`, `2022`, `6m`, `3m`, `1m` | `all` |
| `region` | `ALL`, `Dakar-SN`, `Abidjan-CI`, `Douala-CM`, `Casablanca-MA` | `ALL` |
| `canal` | `ALL`, `B2C GMS`, `B2C Réseau pétrolier`, `B2B Industrie`, `B2B OEM`, `Export` | `ALL` |
| `famille` | `ALL`, `Moteur`, `Hydraulique`, `Transmission`, `Marine`, `Graisse` | `ALL` |

## Lancement local

```bash
uvicorn modules.m7_api.main:app --reload --port 8000
```

Documentation interactive : http://localhost:8000/docs

## Structure

```
modules/m7_api/
├── main.py           # App FastAPI, CORS, routers
├── schemas.py        # Modèles Pydantic (request + response)
├── dependencies.py   # FilterParams, get_data(), get_filtered_raw()
└── routers/
    ├── kpis.py
    ├── products.py
    ├── pricing.py
    ├── forecasts.py
    ├── gap.py
    └── simulate.py
```

## Sécurité

- CORS configurable via `CORS_ORIGINS` (env var) — `localhost:8050` par défaut
- `period` validé avec `Literal` → HTTP 422 si invalide
- `region/canal/famille` limités à 60 caractères
- Méthodes autorisées : GET + POST uniquement
