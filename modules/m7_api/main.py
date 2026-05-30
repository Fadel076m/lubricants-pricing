"""M7 — API FastAPI Lubricants Pricing.

Point d'entrée de l'API REST.

Usage :
    uvicorn modules.m7_api.main:app --reload --port 8000
    python -m modules.m7_api.main
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ajoute la racine du projet au path (même pattern que le dashboard M6)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modules.m7_api.routers import kpis, products, pricing, forecasts, gap, simulate

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "Lubricants Pricing API",
    description = (
        "API REST pour le système de gestion des prix et du portefeuille lubrifiants. "
        "Marchés : Afrique de l'Ouest (XOF) + Maghreb (MAD). "
        "Données synthétiques — jan. 2022 à déc. 2024."
    ),
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    contact     = {"name": "Lubricants Portfolio & Pricing Manager"},
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# En dev : localhost par défaut.
# En prod : définir CORS_ORIGINS=https://lubricants-dash.onrender.com dans les env vars Render.

_DEFAULT_ORIGINS = "http://localhost:8050,http://localhost:8051"
_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins     = _cors_origins,
    allow_methods     = ["GET", "POST"],
    allow_headers     = ["Content-Type", "Accept"],
    allow_credentials = False,
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(kpis.router,      prefix="/api")
app.include_router(products.router,  prefix="/api")
app.include_router(pricing.router,   prefix="/api")
app.include_router(forecasts.router, prefix="/api")
app.include_router(gap.router,       prefix="/api")
app.include_router(simulate.router,  prefix="/api")


# ── Route racine ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "api":     "Lubricants Pricing API",
        "version": "1.0.0",
        "docs":    "/docs",
        "endpoints": [
            "GET  /api/kpis",
            "GET  /api/products",
            "GET  /api/products/{sku_id}",
            "GET  /api/pricing/benchmark",
            "GET  /api/pricing/trend",
            "GET  /api/forecasts",
            "GET  /api/gap/sku",
            "GET  /api/gap/region",
            "POST /api/simulate/pi",
            "POST /api/simulate/scenarios",
        ],
    }


# ── Lancement local ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="M7 — Lubricants Pricing API")
    parser.add_argument("--port",   type=int, default=8000)
    parser.add_argument("--reload", action="store_true", default=True)
    args = parser.parse_args()

    uvicorn.run(
        "modules.m7_api.main:app",
        host    = "0.0.0.0",
        port    = args.port,
        reload  = args.reload,
    )
