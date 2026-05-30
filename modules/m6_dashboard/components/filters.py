"""Global filter components — M6 Dashboard."""

from __future__ import annotations

from dash import dcc, html

from modules.shared.filters_core import apply_filters  # noqa: F401 — re-export

_NAVY = "#0D2B45"
_GREY = "#F4F4F2"

_PERIOD_OPTIONS = [
    {"label": "Toute la période (2022–2024)", "value": "all"},
    {"label": "Année 2024",                   "value": "2024"},
    {"label": "Année 2023",                   "value": "2023"},
    {"label": "Année 2022",                   "value": "2022"},
    {"label": "6 derniers mois",              "value": "6m"},
    {"label": "3 derniers mois",              "value": "3m"},
    {"label": "Dernier mois (déc. 2024)",     "value": "1m"},
]


def _options(values: list) -> list[dict]:
    return [{"label": v, "value": v} for v in sorted(values)]


def filter_bar(
    regions: list[str],
    canaux: list[str],
    familles: list[str],
    component_id_prefix: str = "filter",
) -> html.Div:
    """Barre de filtres : Période · Pays · Canal · Famille de produits."""
    dropdown_style = {"fontSize": "12px", "minWidth": "160px"}

    label_style = {
        "fontSize": "11px", "color": "#7F8C8D", "fontWeight": "700",
        "textTransform": "uppercase", "letterSpacing": "0.5px", "marginBottom": "3px",
    }

    return html.Div(
        children=[
            html.Span("🔍 Filtrer par :", style={
                "fontSize": "12px", "color": "#555", "fontWeight": "600",
                "alignSelf": "center", "whiteSpace": "nowrap",
            }),

            html.Div([
                html.P("Période d'analyse", style=label_style),
                dcc.Dropdown(
                    id=f"{component_id_prefix}-period",
                    options=_PERIOD_OPTIONS,
                    value="all", clearable=False,
                    style={**dropdown_style, "minWidth": "200px"},
                ),
            ], style={"flex": "1.5", "minWidth": "190px"}),

            html.Div([
                html.P("Pays / Région", style=label_style),
                dcc.Dropdown(
                    id=f"{component_id_prefix}-region",
                    options=[{"label": "Tous les pays", "value": "ALL"}] + _options(regions),
                    value="ALL", clearable=False, style=dropdown_style,
                ),
            ], style={"flex": "1", "minWidth": "150px"}),

            html.Div([
                html.P("Canal de vente", style=label_style),
                dcc.Dropdown(
                    id=f"{component_id_prefix}-canal",
                    options=[{"label": "Tous les canaux", "value": "ALL"}] + _options(canaux),
                    value="ALL", clearable=False, style=dropdown_style,
                ),
            ], style={"flex": "1", "minWidth": "150px"}),

            html.Div([
                html.P("Famille de produits", style=label_style),
                dcc.Dropdown(
                    id=f"{component_id_prefix}-famille",
                    options=[{"label": "Toutes les familles", "value": "ALL"}] + _options(familles),
                    value="ALL", clearable=False, style=dropdown_style,
                ),
            ], style={"flex": "1", "minWidth": "150px"}),
        ],
        style={
            "display": "flex", "gap": "16px", "flexWrap": "wrap",
            "backgroundColor": "#EEF2F7",
            "border": "1px solid #D5DCE8",
            "borderRadius": "8px",
            "padding": "14px 18px",
            "marginBottom": "20px",
            "alignItems": "flex-end",
        },
    )


