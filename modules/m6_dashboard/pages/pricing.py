"""Page 2 — Analyse des Prix."""

import dash
from dash import callback, dcc, html, Input, Output

from modules.m6_dashboard.data_loader import load_all
from modules.m6_dashboard.components.kpi_cards import chart_card, info_banner
from modules.m6_dashboard.components.filters import filter_bar, apply_filters
import pandas as pd

from modules.m6_dashboard.components.charts import (
    fig_nsp_vs_concurrent,
    fig_nsp_cogs_trend,
    fig_pi_simulator,
    build_scenarios_comparison,
)

dash.register_page(__name__, path="/pricing", name="Analyse des Prix", order=2)

_NAVY  = "#0D2B45"
_AMBER = "#BA7517"
_GREEN = "#0F6E56"
_RED   = "#993C1D"
_WHITE = "#FFFFFF"


def layout():
    data     = load_all()
    raw      = data.get("raw")
    regions  = sorted(raw["region"].unique())  if raw is not None else []
    canaux   = sorted(raw["canal"].unique())   if raw is not None else []
    familles = sorted(raw["famille"].unique()) if raw is not None else []

    return html.Div([

        # ── En-tête de page ───────────────────────────────────────────────────
        html.Div([
            html.H2("Analyse des Prix", style={"color": _NAVY, "margin": "0", "fontSize": "22px"}),
            html.P(
                "Positionnement tarifaire · Simulateur de hausse de prix · Scénarios",
                style={"color": "#7F8C8D", "fontSize": "13px", "margin": "2px 0 0 0"},
            ),
        ], style={"marginBottom": "20px", "paddingBottom": "16px", "borderBottom": "2px solid #EEE"}),

        # ── Message explicatif ─────────────────────────────────────────────────
        info_banner(
            "💡  Cette page analyse notre stratégie de prix. "
            "Le NSP (Net Selling Price) est le prix réellement payé par le client après remises. "
            "Le COGS est le coût total pour produire et livrer le produit. "
            "Quand le prix du pétrole brut monte, les coûts augmentent — "
            "le simulateur calcule quelle hausse de prix (PI = Price Increase) est nécessaire "
            "pour maintenir notre marge cible.",
            "bleu",
        ),

        # ── Filtres ───────────────────────────────────────────────────────────
        filter_bar(regions, canaux, familles, component_id_prefix="price"),

        # ── Ligne 1 : Prix vs Concurrent + Tendance ───────────────────────────
        html.Div([
            chart_card(
                title="Notre prix vs prix des concurrents",
                description=(
                    "Comparaison entre notre prix de vente net (bleu) et le prix "
                    "pratiqué par la concurrence (orange) sur chaque canal de distribution. "
                    "Idéalement, notre prix doit être compétitif sans sacrifier la marge."
                ),
                chart_id="price-nsp-bench",
                style={"flex": "1"},
            ),
            chart_card(
                title="Évolution prix de vente et coût de revient",
                description=(
                    "La courbe bleue est notre prix de vente, la courbe rouge pointillée est notre "
                    "coût de revient. La zone verte entre les deux représente notre marge. "
                    "Si les deux courbes se rapprochent, la marge est sous pression."
                ),
                chart_id="price-nsp-trend",
                style={"flex": "1"},
            ),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

        # ── Simulateur PI ─────────────────────────────────────────────────────
        html.Div([
            # Titre + explication
            html.Div([
                html.H4(
                    "🎛  Simulateur de hausse de prix (PI)",
                    style={"color": _NAVY, "margin": "0 0 6px 0", "fontSize": "16px"},
                ),
                html.P(
                    "Faites glisser les curseurs, et le classement se met à jour en temps réel. "
                    "Chaque barre = un produit. Plus la barre est longue et rouge, plus la hausse de prix est urgente. "
                    "🔴 = agir immédiatement · 🟡 = surveiller · 🟢 = aucune action nécessaire.",
                    style={"color": "#7F8C8D", "fontSize": "13px", "margin": "0 0 18px 0",
                           "lineHeight": "1.6"},
                ),
            ]),

            # Curseurs
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("Hausse du coût matière (huile de base)", style={
                            "fontSize": "12px", "color": "#555", "fontWeight": "600",
                        }),
                        html.Span(
                            " — ex : si le pétrole augmente de 10%, glissez à 10",
                            style={"fontSize": "11px", "color": "#95A5A6"},
                        ),
                    ], style={"marginBottom": "8px"}),
                    dcc.Slider(
                        id="price-brent-slider",
                        min=0, max=30, step=1, value=10,
                        marks={0: "0%", 5: "5%", 10: "10%", 15: "15%",
                               20: "20%", 25: "25%", 30: "30%"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ], style={"flex": "2", "minWidth": "200px"}),

                html.Div([
                    html.Div([
                        html.Span("Marge brute cible à atteindre", style={
                            "fontSize": "12px", "color": "#555", "fontWeight": "600",
                        }),
                        html.Span(
                            " — objectif recommandé : 30%",
                            style={"fontSize": "11px", "color": "#95A5A6"},
                        ),
                    ], style={"marginBottom": "8px"}),
                    dcc.Slider(
                        id="price-margin-slider",
                        min=15, max=50, step=1, value=30,
                        marks={15: "15%", 20: "20%", 25: "25%",
                               30: "30%", 35: "35%", 40: "40%", 50: "50%"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ], style={"flex": "1", "minWidth": "160px"}),
            ], style={"display": "flex", "gap": "32px", "marginBottom": "20px",
                      "flexWrap": "wrap"}),

            # Légende couleurs
            html.Div([
                html.Span("🔴 Hausse urgente > 5% — à traiter cette semaine",
                          style={"fontSize": "12px", "color": _RED,
                                 "backgroundColor": "#FDEDEC", "padding": "4px 10px",
                                 "borderRadius": "4px", "marginRight": "10px"}),
                html.Span("🟡 Hausse conseillée 2–5% — planifier dans le mois",
                          style={"fontSize": "12px", "color": _AMBER,
                                 "backgroundColor": "#FEF9E7", "padding": "4px 10px",
                                 "borderRadius": "4px", "marginRight": "10px"}),
                html.Span("🟢 Aucune action requise",
                          style={"fontSize": "12px", "color": _GREEN,
                                 "backgroundColor": "#EAFAF1", "padding": "4px 10px",
                                 "borderRadius": "4px"}),
            ], style={"marginBottom": "14px", "flexWrap": "wrap", "display": "flex", "gap": "6px"}),

            dcc.Graph(id="price-pi-scatter", config={"displayModeBar": False}),

        ], style={
            "backgroundColor": _WHITE,
            "borderRadius": "8px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.07)",
            "padding": "24px",
            "marginBottom": "20px",
        }),

        # ── Scénarios ─────────────────────────────────────────────────────────
        html.Div([
            html.H4("Quelle stratégie de prix adopter ?",
                    style={"color": _NAVY, "margin": "0 0 6px 0", "fontSize": "16px"}),
            html.P(
                "Comparez l'impact de 3 choix possibles sur votre profit, volume et marge. "
                "La carte verte est la recommandation. Le graphique montre la variation de profit.",
                style={"color": "#7F8C8D", "fontSize": "12px", "margin": "0 0 8px 0", "lineHeight": "1.6"},
            ),
            # Note explicative — dynamisme
            html.Div([
                html.Span("ℹ️  ", style={"fontSize": "13px"}),
                html.Span(
                    "Ces scénarios sont calculés en temps réel sur les données correspondant "
                    "à vos filtres actifs (période, région, canal). "
                    "Hypothèse : élasticité-prix de −0,5 (une hausse de 10% réduit le volume de 5%). "
                    "Les coûts (COGS) évoluent proportionnellement au volume.",
                    style={"fontSize": "12px", "color": "#555"},
                ),
            ], style={
                "backgroundColor": "#EEF2F7",
                "border": "1px solid #D5DCE8",
                "borderRadius": "6px",
                "padding": "10px 14px",
                "marginBottom": "18px",
                "lineHeight": "1.6",
            }),
            # Conteneur dynamique — mis à jour par callback
            html.Div(id="price-scenarios-container"),
        ], style={
            "backgroundColor": "#FFFFFF",
            "borderRadius": "8px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.07)",
            "padding": "24px",
        }),

    ], style={"padding": "28px", "backgroundColor": "#F5F6FA", "minHeight": "100vh"})


@callback(
    Output("price-nsp-bench", "figure"),
    Output("price-nsp-trend", "figure"),
    Input("price-period",  "value"),
    Input("price-region",  "value"),
    Input("price-canal",   "value"),
    Input("price-famille", "value"),
)
def update_pricing_charts(period, region, canal, famille):
    data     = load_all()
    raw      = data.get("raw")
    filtered = apply_filters(raw, region, canal, famille, period) if raw is not None else None
    return fig_nsp_vs_concurrent(filtered, region), fig_nsp_cogs_trend(filtered)


@callback(
    Output("price-pi-scatter", "figure"),
    Input("price-brent-slider",  "value"),
    Input("price-margin-slider", "value"),
    Input("price-period",        "value"),
    Input("price-region",        "value"),
    Input("price-canal",         "value"),
    Input("price-famille",       "value"),
)
def update_pi_simulator(brent_shock, target_margin, period, region, canal, famille):
    data     = load_all()
    raw      = data.get("raw")
    filtered = apply_filters(raw, region, canal, famille, period) if raw is not None else None
    return fig_pi_simulator(
        filtered,
        brent_shock_pct   = brent_shock / 100,
        target_margin_pct = target_margin / 100,
    )


def _compute_scenarios_from_raw(df: pd.DataFrame) -> pd.DataFrame | None:
    """Calcule les 3 scénarios de prix à la volée sur les données filtrées.

    Hypothèses :
      - Élasticité-prix = -0.5 (hausse de 10% → volume -5%)
      - COGS proportionnel au volume (coûts fixes ignorés)
    """
    if df is None or df.empty:
        return None

    total_ca   = df["ca"].sum()
    total_cogs = (df["ca"] * (1 - df["marge_brute_pct"])).sum()
    old_profit = total_ca - total_cogs
    old_marge  = (total_ca - total_cogs) / total_ca if total_ca > 0 else 0

    ELASTICITY = -0.5
    rows = []
    for scen_id, pi in [("A", 0.03), ("B", 0.05), ("C", 0.00)]:
        vol_factor  = 1 + ELASTICITY * pi
        new_ca      = total_ca * (1 + pi) * vol_factor
        new_cogs    = total_cogs * vol_factor
        new_profit  = new_ca - new_cogs
        new_marge   = (new_ca - new_cogs) / new_ca if new_ca > 0 else 0
        rows.append({
            "scenario":          scen_id,
            "delta_profit_pct":  (new_profit - old_profit) / abs(old_profit) if old_profit else 0,
            "delta_volume_pct":  vol_factor - 1,
            "delta_marge_pts":   new_marge - old_marge,
        })
    return pd.DataFrame(rows)


@callback(
    Output("price-scenarios-container", "children"),
    Input("price-period",  "value"),
    Input("price-region",  "value"),
    Input("price-canal",   "value"),
    Input("price-famille", "value"),
)
def update_scenarios(period, region, canal, famille):
    data     = load_all()
    raw      = data.get("raw")
    filtered = apply_filters(raw, region, canal, famille, period) if raw is not None else None
    scenarios_live = _compute_scenarios_from_raw(filtered)
    return build_scenarios_comparison(scenarios_live)


