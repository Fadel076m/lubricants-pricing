"""Composants KPI — M6 Dashboard."""

from dash import html

_NAVY  = "#0D2B45"
_AMBER = "#BA7517"
_GREEN = "#0F6E56"
_RED   = "#993C1D"
_GREY  = "#F4F4F2"
_WHITE = "#FFFFFF"


def _arrow(delta: float) -> tuple[str, str]:
    if delta > 0:
        return "▲", _GREEN
    if delta < 0:
        return "▼", _RED
    return "–", "#7F8C8D"


def kpi_card(
    label: str,
    value: str,
    delta: float | None = None,
    delta_label: str = "",
    accent_color: str = _NAVY,
    description: str = "",
    delta_suffix: str = "%",
) -> html.Div:
    """Carte KPI avec valeur, flèche delta et description pédagogique."""
    delta_block = []
    if delta is not None:
        sym, color = _arrow(delta)
        sign = "+" if delta > 0 else ""
        delta_block = [
            html.Span(
                f"{sym} {sign}{delta:.1f}{delta_suffix} {delta_label}",
                style={"color": color, "fontSize": "11px", "display": "block",
                       "marginTop": "4px", "fontWeight": "600"},
            )
        ]

    desc_block = []
    if description:
        desc_block = [
            html.P(description, style={
                "color": "#95A5A6", "fontSize": "10px",
                "margin": "6px 0 0 0", "lineHeight": "1.4",
                "borderTop": "1px solid #F0F0F0", "paddingTop": "6px",
            })
        ]

    return html.Div(
        children=[
            html.Div(style={
                "height": "4px",
                "backgroundColor": accent_color,
                "borderRadius": "6px 6px 0 0",
            }),
            html.Div(
                children=[
                    html.P(label, style={
                        "color": "#7F8C8D", "fontSize": "11px",
                        "marginBottom": "4px", "textTransform": "uppercase",
                        "letterSpacing": "0.6px", "fontWeight": "600",
                    }),
                    html.H3(value, style={
                        "color": _NAVY, "fontWeight": "700",
                        "margin": "0", "fontSize": "24px",
                        "letterSpacing": "-0.5px",
                    }),
                    *delta_block,
                    *desc_block,
                ],
                style={"padding": "14px 16px 16px"},
            ),
        ],
        style={
            "backgroundColor": _WHITE,
            "borderRadius": "6px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.07)",
            "flex": "1",
            "minWidth": "170px",
        },
    )


def kpi_row(cards: list) -> html.Div:
    return html.Div(
        children=cards,
        style={"display": "flex", "gap": "14px", "flexWrap": "wrap", "marginBottom": "24px"},
    )


def chart_card(
    title: str,
    description: str,
    chart_id: str,
    style: dict | None = None,
) -> html.Div:
    """Carte conteneur d'un graphique avec titre + explication."""
    from dash import dcc
    outer_style = {
        "backgroundColor": _WHITE,
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.07)",
        "padding": "20px 20px 12px",
        "flex": "1",
        "minWidth": "280px",
    }
    if style:
        outer_style.update(style)

    return html.Div([
        html.Div([
            html.H4(title, style={
                "color": _NAVY, "margin": "0", "fontSize": "14px", "fontWeight": "700",
            }),
            html.P(description, style={
                "color": "#7F8C8D", "fontSize": "12px",
                "margin": "4px 0 12px 0", "lineHeight": "1.5",
            }),
        ]),
        dcc.Graph(id=chart_id, config={"displayModeBar": False}),
    ], style=outer_style)


def alert_badge(text: str, level: str = "rouge") -> html.Span:
    colors = {
        "rouge": (_RED,   "#FDEDEC"),
        "ambre": (_AMBER, "#FEF9E7"),
        "vert":  (_GREEN, "#EAFAF1"),
        "bleu":  ("#2980B9", "#EBF5FB"),
    }
    fg, bg = colors.get(level, ("#7F8C8D", _GREY))
    return html.Span(text, style={
        "backgroundColor": bg, "color": fg,
        "padding": "3px 12px", "borderRadius": "12px",
        "fontWeight": "700", "fontSize": "11px",
    })


def info_banner(text: str, level: str = "bleu") -> html.Div:
    """Bandeau d'information ou d'alerte pédagogique."""
    colors = {
        "bleu":  ("#2980B9", "#EBF5FB", "#2980B9"),
        "rouge": (_RED,      "#FDEDEC", _RED),
        "vert":  (_GREEN,    "#EAFAF1", _GREEN),
        "ambre": (_AMBER,    "#FEF9E7", _AMBER),
    }
    fg, bg, border = colors.get(level, ("#2C3E50", _GREY, "#BDC3C7"))
    return html.Div(text, style={
        "backgroundColor": bg,
        "borderLeft": f"4px solid {border}",
        "color": fg,
        "fontSize": "13px",
        "padding": "10px 16px",
        "borderRadius": "0 6px 6px 0",
        "marginBottom": "16px",
        "lineHeight": "1.6",
    })
