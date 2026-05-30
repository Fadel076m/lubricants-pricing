"""Page 1 — Résumé Général."""

import dash
from dash import callback, html, Input, Output

from modules.m6_dashboard.data_loader import load_all, get_kpi_global
from modules.m6_dashboard.components.kpi_cards import (
    kpi_card, kpi_row, chart_card, alert_badge, info_banner,
)
from modules.m6_dashboard.components.filters import filter_bar, apply_filters
from modules.m6_dashboard.components.charts import (
    fig_ca_evolution,
    fig_ca_by_region,
    fig_top_bottom_skus,
)

dash.register_page(__name__, path="/", name="Résumé Général", order=1)

_NAVY  = "#0D2B45"
_GREEN = "#0F6E56"
_RED   = "#993C1D"
_AMBER = "#BA7517"


def _fmt_vol(v: float) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f} M litres"
    if v >= 1_000:
        return f"{v/1_000:.0f}k litres"
    return f"{v:.0f} litres"


def _fmt_ca(v: float) -> str:
    if v >= 1_000_000_000:
        return f"{v/1_000_000_000:.2f} Md XOF"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f} M XOF"
    if v >= 1_000:
        return f"{v/1_000:.0f}k XOF"
    return f"{v:.0f} XOF"


def layout():
    data     = load_all()
    raw      = data.get("raw")
    kpis     = get_kpi_global(raw) if raw is not None else {}
    regions  = sorted(raw["region"].unique())  if raw is not None else []
    canaux   = sorted(raw["canal"].unique())   if raw is not None else []
    familles = sorted(raw["famille"].unique()) if raw is not None else []

    margins  = data.get("margins")
    n_rouge  = 0
    if margins is not None:
        col    = "marge_brute_pct_moy" if "marge_brute_pct_moy" in margins.columns else "marge_brute_pct"
        n_rouge = int((margins[col] < 0.20).sum())

    return html.Div([

        # ── En-tête de page ───────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H2("Résumé Général", style={"color": _NAVY, "margin": "0", "fontSize": "22px"}),
                html.P(
                    id="exec-header-subtitle",
                    children=f"Vue d'ensemble des performances commerciales · {kpis.get('month_label', '—')}",
                    style={"color": "#7F8C8D", "fontSize": "13px", "margin": "2px 0 0 0"},
                ),
            ]),
            html.Div(
                [alert_badge(f"⚠  {n_rouge} produit(s) en alerte de marge", "rouge")]
                if n_rouge > 0 else [],
                style={"marginLeft": "auto"},
            ),
        ], style={
            "display": "flex", "alignItems": "center", "gap": "16px",
            "marginBottom": "20px", "paddingBottom": "16px",
            "borderBottom": "2px solid #EEE",
        }),

        # ── Message explicatif ─────────────────────────────────────────────────
        info_banner(
            "💡  Cette page présente les indicateurs clés de notre activité lubrifiants "
            "en Afrique de l'Ouest et au Maghreb. "
            "Le chiffre d'affaires (CA) est le total des ventes. "
            "La marge brute indique combien il reste après avoir payé les coûts de production. "
            "Le NSP est le prix net que le client paie effectivement (après remises).",
            "bleu",
        ),

        # ── 4 KPI cards (dynamiques — mise à jour par callback) ───────────────
        html.Div(id="exec-kpi-row"),

        # ── Filtres globaux ───────────────────────────────────────────────────
        filter_bar(regions, canaux, familles, component_id_prefix="exec"),

        # ── Ligne graphiques ──────────────────────────────────────────────────
        html.Div([
            chart_card(
                title="Tendance mensuelle du CA et de la marge",
                description=(
                    "Les barres bleues montrent le chiffre d'affaires chaque mois. "
                    "La courbe orange indique la marge brute (%). "
                    "La ligne pointillée verte marque l'objectif de 30% de marge."
                ),
                chart_id="exec-ca-evolution",
                style={"flex": "2"},
            ),
            chart_card(
                title="CA par zone géographique",
                description=(
                    "Répartition du chiffre d'affaires entre les quatre marchés : "
                    "Sénégal, Côte d'Ivoire, Cameroun et Maroc."
                ),
                chart_id="exec-ca-region",
                style={"flex": "1"},
            ),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "16px"}),

        chart_card(
            title="Produits les plus et les moins rentables",
            description=(
                "Les barres vertes sont les produits qui génèrent la meilleure marge. "
                "Les barres rouges sont ceux dont la marge est insuffisante (< 20%) et qui nécessitent une action. "
                "La ligne pointillée rouge indique le seuil minimum acceptable."
            ),
            chart_id="exec-top-bottom",
        ),

    ], style={"padding": "28px", "backgroundColor": "#F5F6FA", "minHeight": "100vh"})


_PERIOD_LABELS = {
    "all":  "Toute la période (janv. 2022 – déc. 2024)",
    "2024": "Année 2024 (janv. – déc. 2024)",
    "2023": "Année 2023 (janv. – déc. 2023)",
    "2022": "Année 2022 (janv. – déc. 2022)",
    "6m":   "6 derniers mois (juil. – déc. 2024)",
    "3m":   "3 derniers mois (oct. – déc. 2024)",
    "1m":   "Dernier mois (déc. 2024)",
}


@callback(
    Output("exec-ca-evolution",    "figure"),
    Output("exec-ca-region",       "figure"),
    Output("exec-top-bottom",      "figure"),
    Output("exec-header-subtitle", "children"),
    Output("exec-kpi-row",         "children"),
    Input("exec-period",  "value"),
    Input("exec-region",  "value"),
    Input("exec-canal",   "value"),
    Input("exec-famille", "value"),
)
def update_executive(period, region, canal, famille):
    data     = load_all()
    raw      = data.get("raw")
    filtered = apply_filters(raw, region, canal, famille, period) if raw is not None else None
    kpis     = get_kpi_global(filtered) if filtered is not None else {}
    period_txt = _PERIOD_LABELS.get(period, period)
    subtitle   = f"Vue d'ensemble des performances commerciales · {period_txt}"

    kpi_cards = kpi_row([
        kpi_card(
            "Chiffre d'affaires",
            _fmt_ca(kpis.get("ca", 0)),
            kpis.get("ca_delta"),
            "vs mois précédent",
            _NAVY,
            "Revenu total généré par toutes les ventes de lubrifiants.",
        ),
        kpi_card(
            "Volume vendu",
            _fmt_vol(kpis.get("volume", 0)),
            kpis.get("volume_delta"),
            "vs mois précédent",
            "#1A6B9A",
            "Quantité totale de lubrifiants livrée aux clients (en litres).",
        ),
        kpi_card(
            "Marge brute",
            f"{kpis.get('marge', 0):.1f}%",
            kpis.get("marge_delta"),
            "vs mois précédent",
            _GREEN,
            "Part du prix de vente qui reste après les coûts. Objectif : ≥ 30%.",
            delta_suffix=" pts",
        ),
        kpi_card(
            "Prix net moyen (NSP)",
            f"{kpis.get('nsp', 0):,.0f} XOF/L",
            kpis.get("nsp_delta"),
            "vs mois précédent",
            _AMBER,
            "Prix moyen payé par les clients, remises déduites (XOF / litre).",
        ),
    ])

    return (
        fig_ca_evolution(filtered),
        fig_ca_by_region(filtered),
        fig_top_bottom_skus(filtered),
        subtitle,
        kpi_cards,
    )
