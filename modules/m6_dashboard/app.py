"""M6 — Executive Dashboard Plotly Dash.

Point d'entrée de l'application multi-pages.

Usage :
    python -m modules.m6_dashboard.app
    python -m modules.m6_dashboard.app --port 8051 --debug
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ajoute la racine du projet au path AVANT que Dash charge les pages
# (nécessaire car Dash importe les fichiers pages/ via importlib en dehors du package)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import dash
from dash import Dash, dcc, html, Input, Output, page_container
from loguru import logger

# ── Palette ───────────────────────────────────────────────────────────────────
_NAVY   = "#0D2B45"
_AMBER  = "#BA7517"
_WHITE  = "#FFFFFF"
_GREY   = "#F4F4F2"

# ── Initialisation ────────────────────────────────────────────────────────────
_PAGES_DIR = Path(__file__).parent / "pages"

app = Dash(
    __name__,
    use_pages=True,
    pages_folder=str(_PAGES_DIR),
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    title="Lubricants Pricing Dashboard",
)

# ── Navbar ────────────────────────────────────────────────────────────────────

def _nav_link(page: dict) -> html.A:
    return html.A(
        page["name"],
        href=page["relative_path"],
        style={
            "color": "rgba(255,255,255,0.85)",
            "textDecoration": "none",
            "padding": "6px 14px",
            "borderRadius": "4px",
            "fontSize": "13px",
            "fontWeight": "500",
            "transition": "background 0.15s",
        },
        id=f"nav-{page['module']}",
    )


navbar = html.Nav(
    children=[
        # Logo / titre
        html.Div([
            html.Span("⚡", style={"fontSize": "18px", "marginRight": "8px"}),
            html.Span(
                "Lubricants Pricing",
                style={"fontWeight": "700", "fontSize": "15px", "color": _WHITE},
            ),
        ], style={"display": "flex", "alignItems": "center", "gap": "4px"}),

        # Liens de navigation (générés depuis pages/)
        html.Div(
            id="nav-links",
            style={"display": "flex", "gap": "4px"},
        ),

        # Indicateur marché
        html.Div(
            "Afrique de l'Ouest · Maghreb · Données synthétiques",
            style={"color": "rgba(255,255,255,0.45)", "fontSize": "11px",
                   "marginLeft": "auto", "whiteSpace": "nowrap"},
        ),
    ],
    style={
        "backgroundColor":  _NAVY,
        "display":          "flex",
        "alignItems":       "center",
        "padding":          "0 24px",
        "height":           "52px",
        "gap":              "20px",
        "boxShadow":        "0 2px 8px rgba(0,0,0,0.15)",
        "position":         "sticky",
        "top":              "0",
        "zIndex":           "1000",
    },
)


# ── Layout racine ─────────────────────────────────────────────────────────────

app.layout = html.Div([
    dcc.Location(id="url"),
    navbar,
    page_container,
], style={"fontFamily": "Inter, Arial, sans-serif", "backgroundColor": "#FAFAFA"})


# ── Callback : liens navbar actifs ────────────────────────────────────────────

@app.callback(
    Output("nav-links", "children"),
    Input("url", "pathname"),
)
def update_nav(pathname):
    links = []
    for page in dash.page_registry.values():
        is_active = pathname == page["relative_path"]
        style = {
            "color":          _WHITE if not is_active else _AMBER,
            "textDecoration": "none",
            "padding":        "6px 14px",
            "borderRadius":   "4px",
            "fontSize":       "13px",
            "fontWeight":     "600" if is_active else "400",
            "backgroundColor": "rgba(255,255,255,0.12)" if is_active else "transparent",
        }
        links.append(html.A(page["name"], href=page["relative_path"], style=style))
    return links


# ── Serveur WSGI (pour Gunicorn / Render.com) ─────────────────────────────────
server = app.server


# ── Lancement local ──────────────────────────────────────────────────────────

def _run(port: int = 8050, debug: bool = True) -> None:
    from .data_loader import load_all
    logger.info("Pré-chargement des données…")
    load_all()
    logger.success("Démarrage du dashboard sur http://localhost:{}/", port)
    app.run(debug=debug, port=port, host="0.0.0.0")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="M6 — Lubricants Dashboard")
    parser.add_argument("--port",  type=int, default=8050)
    parser.add_argument("--debug", action="store_true", default=True)
    args = parser.parse_args()
    _run(port=args.port, debug=args.debug)
