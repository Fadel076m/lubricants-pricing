"""Page 3 — Portefeuille Produits."""

import io

import dash
from dash import callback, dash_table, dcc, html, Input, Output
import pandas as pd

from modules.m6_dashboard.data_loader import load_all
from modules.m6_dashboard.components.kpi_cards import chart_card, info_banner, alert_badge
from modules.m6_dashboard.components.filters import filter_bar, apply_filters
from modules.m6_dashboard.components.charts import fig_bcg_matrix, fig_gap_skus

dash.register_page(__name__, path="/portfolio", name="Portefeuille Produits", order=3)

_NAVY  = "#0D2B45"
_RED   = "#993C1D"
_AMBER = "#BA7517"
_GREEN = "#0F6E56"
_WHITE = "#FFFFFF"


def _alert_skus(raw: pd.DataFrame | None) -> list:
    if raw is None:
        return []
    raw = raw.copy()
    raw["date"] = pd.to_datetime(raw["date"])
    cutoff = raw["date"].max() - pd.Timedelta(days=30)
    recent = raw[raw["date"] >= cutoff]
    at_risk = (
        recent.groupby("sku_id")["marge_brute_pct"]
        .mean().reset_index()
        .query("marge_brute_pct < 0.20")
        .sort_values("marge_brute_pct")
    )
    return at_risk["sku_id"].tolist()


def _build_export_table(raw: pd.DataFrame | None) -> pd.DataFrame:
    if raw is None:
        return pd.DataFrame()

    data  = load_all()
    fc_df = data.get("forecasts")
    gap_df = data.get("gap_sku")

    base = (
        raw.groupby(["sku_id", "canal", "region"])
        .agg(
            nsp_moy  =("nsp",             "mean"),
            marge_pct=("marge_brute_pct", "mean"),
            volume   =("volume_vendu",    "sum"),
        )
        .reset_index()
    )
    base["nsp_moy"]   = base["nsp_moy"].round(1)
    base["marge_pct"] = (base["marge_pct"] * 100).round(1)
    base["volume"]    = base["volume"].round(0).astype(int)

    if fc_df is not None:
        fc_vol = fc_df[
            (fc_df["target"] == "volume_vendu") & (fc_df["horizon_days"] == 30)
        ]
        if len(fc_vol) == 1:
            base["Prévision +30j (L)"] = int(fc_vol["yhat"].iloc[0])
        else:
            base["Prévision +30j (L)"] = None
    else:
        base["Prévision +30j (L)"] = None

    if gap_df is not None and "sku_code" in gap_df.columns:
        gap_avg = (
            gap_df.groupby("sku_code")["gap_rel"]
            .mean().reset_index()
            .rename(columns={"sku_code": "sku_id", "gap_rel": "ecart_pct"})
        )
        gap_avg["ecart_pct"] = (gap_avg["ecart_pct"] * 100).round(1)
        base = base.merge(gap_avg, on="sku_id", how="left")
    else:
        base["ecart_pct"] = None

    return base.rename(columns={
        "sku_id":   "Produit (SKU)",
        "canal":    "Canal",
        "region":   "Région",
        "nsp_moy":  "Prix net moy. (XOF/L)",
        "marge_pct":"Marge brute (%)",
        "volume":   "Volume vendu (L)",
        "ecart_pct":"Écart vs prévision (%)",
    })


def layout():
    data     = load_all()
    raw      = data.get("raw")
    regions  = sorted(raw["region"].unique())  if raw is not None else []
    canaux   = sorted(raw["canal"].unique())   if raw is not None else []
    familles = sorted(raw["famille"].unique()) if raw is not None else []

    return html.Div([

        # ── En-tête de page ───────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H2("Portefeuille Produits", style={"color": _NAVY, "margin": "0", "fontSize": "22px"}),
                html.P(
                    "Carte des produits · Analyse des écarts · Tableau de bord détaillé",
                    style={"color": "#7F8C8D", "fontSize": "13px", "margin": "2px 0 0 0"},
                ),
            ]),
            # Badge dynamique — mis à jour par callback
            html.Div(id="port-alert-badge", style={"marginLeft": "auto"}),
        ], style={
            "display": "flex", "alignItems": "center", "gap": "16px",
            "marginBottom": "20px", "paddingBottom": "16px",
            "borderBottom": "2px solid #EEE",
        }),

        # ── Message explicatif ─────────────────────────────────────────────────
        info_banner(
            "💡  Cette page analyse l'ensemble du catalogue produits. "
            "La carte des produits classe chaque lubrifiant selon deux axes : "
            "combien on en vend (volume) et combien on gagne dessus (marge). "
            "L'analyse des écarts compare les ventes réelles aux prévisions du modèle ML.",
            "bleu",
        ),

        # ── Alerte SKUs critiques (dynamique) ────────────────────────────────
        html.Div(id="port-alert-panel", style={"marginBottom": "16px"}),

        # ── Filtres ───────────────────────────────────────────────────────────
        filter_bar(regions, canaux, familles, component_id_prefix="port"),

        # ── Carte BCG + Écarts ────────────────────────────────────────────────
        html.Div([
            chart_card(
                title="Carte des produits — Volume vs Rentabilité",
                description=(
                    "Chaque point est un produit. "
                    "⭐ Stars (vert) : forts volumes et bonne marge — à protéger. "
                    "🐄 Vaches à lait (orange) : bonne marge mais peu vendus — potentiel de croissance. "
                    "🔵 Dilemmes (bleu) : très vendus mais marge trop faible — action prix urgente. "
                    "🔴 Poids morts (rouge) : faible volume ET faible marge — à réévaluer."
                ),
                chart_id="port-bcg",
                style={"flex": "1"},
            ),
            chart_card(
                title="Fiabilité des prévisions de vente par produit",
                description=(
                    "Chaque barre = % de mois où le produit a vendu autant que prévu (±5%). "
                    "🟢 Vert ≥ 70% : prévisions fiables — pas d'action. "
                    "🟡 Orange 50–70% : performances irrégulières — surveiller. "
                    "🔴 Rouge < 50% : manque la cible un mois sur deux — réviser le plan ou le prix."
                ),
                chart_id="port-gap-sku",
                style={"flex": "1"},
            ),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

        # ── Tableau détaillé + Export ─────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div([
                    html.H4("Tableau détaillé de tous les produits",
                            style={"color": _NAVY, "margin": "0", "fontSize": "14px"}),
                    html.P(
                        "Filtrez et triez les colonnes. Cliquez sur Exporter pour télécharger en Excel.",
                        style={"color": "#7F8C8D", "fontSize": "11px", "margin": "2px 0 0 0"},
                    ),
                ]),
                html.Button(
                    "⬇  Exporter en Excel",
                    id="port-export-btn",
                    n_clicks=0,
                    style={
                        "backgroundColor": _NAVY, "color": _WHITE,
                        "border": "none", "padding": "8px 18px",
                        "borderRadius": "5px", "cursor": "pointer",
                        "fontSize": "12px", "fontWeight": "600",
                        "marginLeft": "auto",
                    },
                ),
            ], style={"display": "flex", "alignItems": "center",
                      "justifyContent": "space-between", "marginBottom": "14px"}),

            dcc.Download(id="port-download"),

            # Légende colonnes
            html.Div([
                html.Span("Colonnes : ", style={"fontWeight": "600", "fontSize": "11px", "color": "#555"}),
                html.Span("Prix net moy. = NSP moyen sur la période  ·  ",
                          style={"fontSize": "11px", "color": "#7F8C8D"}),
                html.Span("Marge brute = profit après coûts de production  ·  ",
                          style={"fontSize": "11px", "color": "#7F8C8D"}),
                html.Span("Écart = différence réel vs prévision ML",
                          style={"fontSize": "11px", "color": "#7F8C8D"}),
            ], style={"marginBottom": "10px"}),

            dash_table.DataTable(
                id="port-table",
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": _NAVY,
                    "color": _WHITE,
                    "fontWeight": "700",
                    "fontSize": "12px",
                    "padding": "10px 14px",
                    "textAlign": "left",
                },
                style_cell={
                    "fontSize": "12px",
                    "padding": "8px 14px",
                    "fontFamily": "Inter, Arial, sans-serif",
                    "border": "1px solid #E8E8E8",
                    "textAlign": "left",
                },
                style_data={"backgroundColor": _WHITE},
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "#F8F9FA",
                    },
                    {
                        "if": {"filter_query": "{Marge brute (%)} < 20",
                               "column_id": "Marge brute (%)"},
                        "backgroundColor": "#FDEDEC",
                        "color": _RED,
                        "fontWeight": "700",
                    },
                    {
                        "if": {"filter_query": "{Marge brute (%)} >= 30",
                               "column_id": "Marge brute (%)"},
                        "color": _GREEN,
                        "fontWeight": "600",
                    },
                    {
                        "if": {"filter_query": "{Écart vs prévision (%)} < -5",
                               "column_id": "Écart vs prévision (%)"},
                        "backgroundColor": "#FEF9E7",
                        "color": _AMBER,
                    },
                ],
                page_size=15,
                sort_action="native",
                filter_action="native",
                tooltip_header={
                    "Marge brute (%)": "Part du prix de vente restant après les coûts. Objectif ≥ 30%",
                    "Écart vs prévision (%)": "Positif = on a vendu plus que prévu. Négatif = moins que prévu.",
                    "Prix net moy. (XOF/L)": "Prix payé par le client en devise locale, par litre.",
                },
                tooltip_delay=0,
                tooltip_duration=None,
            ),
        ], style={
            "backgroundColor": _WHITE,
            "borderRadius": "8px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.07)",
            "padding": "22px",
        }),

    ], style={"padding": "28px", "backgroundColor": "#F5F6FA", "minHeight": "100vh"})


def _filter_gap_sku(gap_sku: pd.DataFrame, filtered_raw: pd.DataFrame, period: str) -> pd.DataFrame:
    """Filtre gap_sku par les SKUs présents dans filtered_raw et par la période."""
    if gap_sku is None:
        return gap_sku
    df = gap_sku.copy()

    # Filtrer par SKUs présents dans les données brutes filtrées
    if filtered_raw is not None and not filtered_raw.empty:
        sku_ids = filtered_raw["sku_id"].unique()
        df = df[df["sku_code"].isin(sku_ids)]

    # Filtrer par période
    if period != "all" and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        if period == "2024":
            df = df[df["date"].dt.year == 2024]
        elif period == "2023":
            df = df[df["date"].dt.year == 2023]
        elif period == "2022":
            df = df[df["date"].dt.year == 2022]
        elif period in ("1m", "3m", "6m"):
            max_date = pd.to_datetime(gap_sku["date"]).max()
            months = {"1m": 1, "3m": 3, "6m": 6}[period]
            cutoff = max_date - pd.DateOffset(months=months)
            df = df[df["date"] > cutoff]

    return df if not df.empty else gap_sku


def _build_alert_children(at_risk: list) -> tuple:
    """Construit le badge et le panneau d'alerte SKU."""
    if at_risk:
        badge = [alert_badge(f"⚠  {len(at_risk)} produit(s) sous le seuil critique de marge", "rouge")]
        panel = html.Div([
            html.Span("⚠  Produits en alerte marge (< 20% sur la période) : ",
                      style={"fontWeight": "700", "color": _RED, "fontSize": "13px"}),
            html.Span(
                ", ".join(s.replace("SKU-", "") for s in at_risk[:10]),
                style={"fontSize": "13px", "color": _RED},
            ),
            html.Br(),
            html.Span(
                "→ Action recommandée : réviser le prix de vente ou négocier les coûts d'approvisionnement.",
                style={"fontSize": "11px", "color": "#7F8C8D", "marginTop": "4px", "display": "block"},
            ),
        ], style={
            "backgroundColor": "#FDEDEC",
            "borderLeft": f"4px solid {_RED}",
            "padding": "12px 18px",
            "borderRadius": "0 6px 6px 0",
        })
    else:
        badge = [alert_badge("✓  Tous les produits sont au-dessus du seuil critique", "vert")]
        panel = html.Div([
            html.Span("✓  Aucun produit en alerte marge sur la période sélectionnée.",
                      style={"fontSize": "13px", "color": _GREEN, "fontWeight": "600"}),
        ], style={
            "backgroundColor": "#EAFAF1",
            "borderLeft": f"4px solid {_GREEN}",
            "padding": "12px 18px",
            "borderRadius": "0 6px 6px 0",
        })
    return badge, panel


@callback(
    Output("port-bcg",          "figure"),
    Output("port-gap-sku",      "figure"),
    Output("port-table",        "data"),
    Output("port-table",        "columns"),
    Output("port-alert-badge",  "children"),
    Output("port-alert-panel",  "children"),
    Input("port-period",   "value"),
    Input("port-region",   "value"),
    Input("port-canal",    "value"),
    Input("port-famille",  "value"),
)
def update_portfolio(period, region, canal, famille):
    data     = load_all()
    raw      = data.get("raw")
    gap_sku  = data.get("gap_sku")
    filtered = apply_filters(raw, region, canal, famille, period) if raw is not None else None

    gap_filtered = _filter_gap_sku(gap_sku, filtered, period)
    at_risk      = _alert_skus(filtered)
    badge, panel = _build_alert_children(at_risk)

    export_df = _build_export_table(filtered)
    columns   = [{"name": c, "id": c} for c in export_df.columns]
    records   = export_df.to_dict("records")
    return fig_bcg_matrix(filtered), fig_gap_skus(gap_filtered), records, columns, badge, panel


@callback(
    Output("port-download", "data"),
    Input("port-export-btn", "n_clicks"),
    Input("port-period",     "value"),
    Input("port-region",     "value"),
    Input("port-canal",      "value"),
    Input("port-famille",    "value"),
    prevent_initial_call=True,
)
def export_excel(n_clicks, period, region, canal, famille):
    from dash import ctx
    if ctx.triggered_id != "port-export-btn" or not n_clicks:
        return dash.no_update
    data     = load_all()
    raw      = data.get("raw")
    filtered = apply_filters(raw, region, canal, famille, period) if raw is not None else None
    df       = _build_export_table(filtered)
    buf      = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return dcc.send_bytes(buf.read(), filename="portefeuille_produits.xlsx")
