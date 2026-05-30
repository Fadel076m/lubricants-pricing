"""Graphiques Plotly réutilisables — M6 Dashboard (tout en français)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_NAVY   = "#0D2B45"
_AMBER  = "#BA7517"
_GREEN  = "#0F6E56"
_RED    = "#993C1D"
_GREY   = "#F4F4F2"
_GREY2  = "#7F8C8D"
_BLUE   = "#1A6B9A"
_WHITE  = "#FFFFFF"

_TEMPLATE = "plotly_white"
_FONT     = dict(family="Inter, Arial, sans-serif", size=12, color=_NAVY)
_MARGIN   = dict(l=55, r=20, t=55, b=45)


def _empty(msg: str = "Données non disponibles") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=14, color=_GREY2),
    )
    fig.update_layout(
        template=_TEMPLATE, paper_bgcolor="#F8F8F8",
        plot_bgcolor="#F8F8F8", margin=_MARGIN,
    )
    return fig


# ════════════════════════════════════════════════════════════════
# PAGE RÉSUMÉ GÉNÉRAL
# ════════════════════════════════════════════════════════════════

def fig_ca_evolution(raw: pd.DataFrame) -> go.Figure:
    """Chiffre d'affaires mensuel + marge brute sur 12 mois."""
    if raw is None or raw.empty:
        return _empty()

    monthly = (
        raw.groupby("month")
        .agg(ca=("ca", "sum"), marge=("marge_brute_pct", "mean"))
        .reset_index()
        .sort_values("month")
        .tail(12)
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=monthly["month"],
        y=monthly["ca"],
        name="Chiffre d'affaires",
        marker_color=_NAVY,
        opacity=0.85,
        hovertemplate="<b>%{x|%b %Y}</b><br>CA : %{y:,.0f} XOF<extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=monthly["month"],
        y=monthly["marge"] * 100,
        name="Marge brute (%)",
        mode="lines+markers",
        line=dict(color=_AMBER, width=2.5),
        marker=dict(size=6, color=_AMBER),
        hovertemplate="<b>%{x|%b %Y}</b><br>Marge : %{y:.1f}%<extra></extra>",
    ), secondary_y=True)

    # Ligne objectif marge 30%
    fig.add_hline(
        y=30, line_dash="dot", line_color=_GREEN, line_width=1,
        annotation_text="Objectif 30%", annotation_position="right",
        annotation_font_size=10, annotation_font_color=_GREEN,
        secondary_y=True,
    )

    fig.update_layout(
        title=dict(text="Évolution du chiffre d'affaires et de la marge brute", font=dict(size=14)),
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=55, r=20, t=55, b=70),
        legend=dict(orientation="h", y=-0.18, x=0, yanchor="top", font=dict(size=11)),
        hovermode="x unified",
        plot_bgcolor="#FAFAFA",
    )
    fig.update_yaxes(title_text="CA (XOF)", secondary_y=False)
    fig.update_yaxes(
        title_text="Marge brute (%)", secondary_y=True,
        ticksuffix="%", showgrid=False, range=[0, 60],
    )
    return fig


def _fmt_ca_label(v: float, pct: float) -> str:
    """Formatte un montant CA avec la bonne unité et le pourcentage."""
    if v >= 1e9:
        return f"{v/1e9:.1f} Md XOF  ({pct:.0f}%)"
    if v >= 1e6:
        return f"{v/1e6:.0f} M XOF  ({pct:.0f}%)"
    return f"{v:,.0f} XOF  ({pct:.0f}%)"


def fig_ca_by_region(raw: pd.DataFrame) -> go.Figure:
    """Chiffre d'affaires total par région géographique."""
    if raw is None or raw.empty:
        return _empty()

    by_region = (
        raw.groupby("region")["ca"]
        .sum().reset_index()
        .sort_values("ca", ascending=True)
    )
    total = by_region["ca"].sum()
    by_region["pct"] = by_region["ca"] / total * 100

    n = len(by_region)
    colors = [_NAVY, _BLUE, _AMBER, _GREEN][:n]

    fig = go.Figure(go.Bar(
        x=by_region["ca"],
        y=by_region["region"],
        orientation="h",
        marker_color=colors,
        text=[_fmt_ca_label(v, p) for v, p in zip(by_region["ca"], by_region["pct"])],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>CA : %{x:,.0f} XOF<extra></extra>",
    ))

    # Étendre l'axe x pour que les labels ne soient pas coupés
    x_max = by_region["ca"].max()
    fig.update_xaxes(range=[0, x_max * 1.45])

    fig.update_layout(
        title=dict(text="CA par zone géographique", font=dict(size=14)),
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=110, r=20, t=55, b=40),
        height=max(260, n * 60 + 100),
        showlegend=False,
        plot_bgcolor="#FAFAFA",
    )
    return fig


def fig_top_bottom_skus(raw_or_margins: pd.DataFrame, n: int = 5) -> go.Figure:
    """Meilleurs et moins bons produits par marge brute.

    Accepte soit les données brutes (raw transactions) soit le parquet margins_by_sku.
    Si raw_or_margins contient la colonne 'ca', calcule la marge agrégée par SKU à la volée.
    """
    if raw_or_margins is None or raw_or_margins.empty:
        return _empty()

    if "ca" in raw_or_margins.columns:
        # Données brutes → agréger par SKU
        sku_df = (
            raw_or_margins.groupby("sku_id")["marge_brute_pct"]
            .mean()
            .reset_index()
            .rename(columns={"sku_id": "_sku", "marge_brute_pct": "_marge"})
        )
        col_s, col_m = "_sku", "_marge"
    else:
        col_m = "marge_brute_pct_moy" if "marge_brute_pct_moy" in raw_or_margins.columns else "marge_brute_pct"
        col_s = "sku_id" if "sku_id" in raw_or_margins.columns else raw_or_margins.columns[0]
        sku_df = raw_or_margins.rename(columns={col_s: "_sku", col_m: "_marge"})
        col_s, col_m = "_sku", "_marge"

    df     = sku_df[["_sku", "_marge"]].dropna().sort_values("_marge")
    bottom = df.head(n).copy()
    top    = df.tail(n).copy()
    combined = pd.concat([bottom, top]).drop_duplicates("_sku")

    colors = [
        _RED if v < 0.20 else (_AMBER if v < 0.30 else _GREEN)
        for v in combined["_marge"]
    ]

    fig = go.Figure(go.Bar(
        x=combined["_marge"] * 100,
        y=combined["_sku"].str.replace("SKU-", "", regex=False),
        orientation="h",
        marker_color=colors,
        text=[f"  {v*100:.1f}%" for v in combined["_marge"]],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Marge brute : %{x:.1f}%<extra></extra>",
    ))

    fig.add_vline(x=20, line_dash="dash", line_color=_RED, line_width=1.5,
                  annotation_text="Seuil critique 20%",
                  annotation_font_size=10, annotation_font_color=_RED)
    fig.add_vline(x=30, line_dash="dash", line_color=_AMBER, line_width=1.5,
                  annotation_text="Objectif 30%",
                  annotation_font_size=10, annotation_font_color=_AMBER)

    fig.update_xaxes(range=[0, combined["_marge"].max() * 130])

    fig.update_layout(
        title=dict(text=f"Top {n} produits rentables & bottom {n} en difficulté", font=dict(size=14)),
        xaxis_title="Marge brute (%)",
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=160, r=20, t=55, b=45),
        height=380,
        showlegend=False,
        plot_bgcolor="#FAFAFA",
    )
    return fig


# ════════════════════════════════════════════════════════════════
# PAGE ANALYSE DES PRIX
# ════════════════════════════════════════════════════════════════

def fig_nsp_vs_concurrent(raw: pd.DataFrame, region: str = "ALL") -> go.Figure:
    """Comparaison du prix de vente net vs prix du concurrent par canal."""
    if raw is None or raw.empty:
        return _empty()

    df = raw if region == "ALL" else raw[raw["region"] == region]
    by_canal = (
        df.groupby("canal")
        .agg(nsp=("nsp", "mean"), concurrent=("prix_concurrent", "mean"))
        .reset_index()
        .sort_values("nsp", ascending=False)
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Notre prix net (NSP)",
        x=by_canal["canal"], y=by_canal["nsp"],
        marker_color=_NAVY,
        hovertemplate="<b>%{x}</b><br>Notre prix net : %{y:,.0f} XOF/L<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Prix concurrent",
        x=by_canal["canal"], y=by_canal["concurrent"],
        marker_color=_AMBER,
        hovertemplate="<b>%{x}</b><br>Prix concurrent : %{y:,.0f} XOF/L<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="Notre prix de vente vs prix des concurrents", font=dict(size=14)),
        yaxis_title="Prix net moyen (XOF / litre)",
        barmode="group",
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=55, r=20, t=55, b=70),
        legend=dict(orientation="h", y=-0.18, x=0, yanchor="top", font=dict(size=11)),
        plot_bgcolor="#FAFAFA",
    )
    return fig


def fig_nsp_cogs_trend(raw: pd.DataFrame) -> go.Figure:
    """Évolution du prix de vente et du coût de revient sur 36 mois."""
    if raw is None or raw.empty:
        return _empty()

    monthly = (
        raw.groupby("month")
        .agg(nsp=("nsp", "mean"), cogs=("cogs_total", "mean"))
        .reset_index()
        .sort_values("month")
    )
    monthly["ecart"] = monthly["nsp"] - monthly["cogs"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["nsp"],
        name="Prix de vente net (NSP)",
        mode="lines+markers",
        line=dict(color=_NAVY, width=2.5),
        marker=dict(size=5),
        hovertemplate="<b>%{x|%b %Y}</b><br>Prix vente : %{y:,.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["cogs"],
        name="Coût de revient (COGS)",
        mode="lines+markers",
        line=dict(color=_RED, width=2, dash="dash"),
        marker=dict(size=5),
        hovertemplate="<b>%{x|%b %Y}</b><br>Coût revient : %{y:,.1f}<extra></extra>",
    ))
    # Zone de marge
    fig.add_trace(go.Scatter(
        x=list(monthly["month"]) + list(monthly["month"][::-1]),
        y=list(monthly["nsp"]) + list(monthly["cogs"][::-1]),
        fill="toself",
        fillcolor="rgba(15,110,86,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Zone de marge",
        hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(text="Prix de vente et coût de revient (36 mois)", font=dict(size=14)),
        xaxis_title="Mois",
        yaxis_title="Valeur (XOF / litre)",
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=55, r=20, t=55, b=70),
        legend=dict(orientation="h", y=-0.18, x=0, yanchor="top", font=dict(size=11)),
        hovermode="x unified",
        plot_bgcolor="#FAFAFA",
    )
    return fig


def fig_pi_simulator(
    raw: pd.DataFrame,
    brent_shock_pct: float = 0.10,
    target_margin_pct: float = 0.30,
) -> go.Figure:
    """Classement des produits par urgence de hausse de prix — lecture immédiate."""
    if raw is None or raw.empty:
        return _empty()

    grp = (
        raw.groupby("sku_id")
        .agg(
            nsp            =("nsp",             "mean"),
            cogs           =("cogs_total",       "mean"),
            cout_huile_base=("cout_huile_base",  "mean"),
            marge          =("marge_brute_pct",  "mean"),
            canal_top      =("canal",            lambda x: x.value_counts().index[0]),
        )
        .reset_index()
    )

    grp["cogs_new"]  = grp["cogs"] + grp["cout_huile_base"] * brent_shock_pct
    grp["nsp_cible"] = grp["cogs_new"] / (1 - target_margin_pct)
    grp["pi_requis"] = (grp["nsp_cible"] / grp["nsp"] - 1) * 100
    grp["marge_pct"] = grp["marge"] * 100

    grp["urgence"] = grp["pi_requis"].apply(
        lambda v: "🔴 Hausse urgente" if v > 5 else (
            "🟡 Hausse conseillée" if v > 2 else "🟢 Aucune action requise"
        )
    )
    grp["couleur"] = grp["pi_requis"].apply(
        lambda v: _RED if v > 5 else (_AMBER if v > 2 else _GREEN)
    )

    # Trier par PI décroissant, ne garder que les produits qui ont besoin d'action
    df_action = grp[grp["pi_requis"] > 0].sort_values("pi_requis", ascending=True)

    if df_action.empty:
        df_action = grp.sort_values("pi_requis", ascending=True)

    # Nom court lisible
    df_action["nom"] = (
        df_action["sku_id"].str.replace("SKU-", "", regex=False)
        + "  (" + df_action["canal_top"] + ")"
    )

    fig = go.Figure(go.Bar(
        x=df_action["pi_requis"],
        y=df_action["nom"],
        orientation="h",
        marker_color=df_action["couleur"],
        text=[f"+{v:.1f}%" if v > 0 else f"{v:.1f}%" for v in df_action["pi_requis"]],
        textposition="outside",
        textfont=dict(size=11),
        customdata=df_action[["marge_pct", "urgence"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Hausse de prix à appliquer : <b>%{x:.1f}%</b><br>"
            "Marge actuelle : %{customdata[0]:.1f}%<br>"
            "Statut : %{customdata[1]}<extra></extra>"
        ),
    ))

    # Ligne zéro
    fig.add_vline(x=0, line_color=_NAVY, line_width=1.5)

    # Zone d'action urgente
    max_x = max(df_action["pi_requis"].max() * 1.2, 10)
    fig.add_vrect(
        x0=5, x1=max_x,
        fillcolor="rgba(153,60,29,0.05)",
        layer="below", line_width=0,
        annotation_text="Zone urgente", annotation_position="top right",
        annotation_font_size=10, annotation_font_color=_RED,
    )
    fig.add_vrect(
        x0=2, x1=5,
        fillcolor="rgba(186,117,23,0.05)",
        layer="below", line_width=0,
    )

    # Lignes de seuil
    fig.add_vline(x=5, line_dash="dot", line_color=_RED, line_width=1.5)
    fig.add_vline(x=2, line_dash="dot", line_color=_AMBER, line_width=1.5)

    n_urgent  = int((df_action["pi_requis"] > 5).sum())
    n_modere  = int(((df_action["pi_requis"] > 2) & (df_action["pi_requis"] <= 5)).sum())

    fig.update_layout(
        title=dict(
            text=(
                f"Hausse de prix à appliquer par produit "
                f"(choc coûts +{brent_shock_pct*100:.0f}% · objectif marge {target_margin_pct*100:.0f}%)  —  "
                f"🔴 {n_urgent} urgents · 🟡 {n_modere} modérés"
            ),
            font=dict(size=13),
        ),
        xaxis_title="Hausse de prix à appliquer (%)",
        xaxis_ticksuffix="%",
        yaxis_title="",
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=250, r=80, t=70, b=50),
        height=max(380, len(df_action) * 28 + 100),
        showlegend=False,
        plot_bgcolor="#FAFAFA",
    )
    return fig


def build_scenarios_comparison(scenarios_df: pd.DataFrame):
    """Composant Dash : 3 cartes de comparaison + graphique profit simplifié.

    Retourne un html.Div (pas un go.Figure) pour une lisibilité maximale.
    """
    from dash import html, dcc

    # ── Valeurs par défaut si données absentes ────────────────────────────────
    if scenarios_df is None or scenarios_df.empty or "scenario" not in scenarios_df.columns:
        return html.Div("Scénarios non disponibles — lancer d'abord run_m3.py",
                        style={"color": _GREY2, "padding": "20px"})

    agg = scenarios_df.groupby("scenario")[
        ["delta_profit_pct", "delta_volume_pct", "delta_marge_pts"]
    ].mean()

    def _pct(val, scale=100):
        v = val * scale
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.1f}%"

    def _pts(val, scale=100):
        v = val * scale
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.1f} pts"

    def _color(val):
        return _GREEN if val > 0 else (_RED if val < -0.05 else _AMBER)

    # ── Config des 3 scénarios ────────────────────────────────────────────────
    scenarios_config = {
        "A": {
            "titre":    "Scénario A",
            "sous":     "Hausse des prix de 3%",
            "verdict":  "Insuffisant",
            "verdict_color": _AMBER,
            "verdict_bg":    "#FEF9E7",
            "icone":    "⚠️",
            "message":  "Profit en baisse malgré la hausse — les coûts augmentent plus vite.",
        },
        "B": {
            "titre":    "Scénario B",
            "sous":     "Hausse des prix de 5%",
            "verdict":  "RECOMMANDÉ ★",
            "verdict_color": _WHITE,
            "verdict_bg":    _GREEN,
            "icone":    "✅",
            "message":  "Seul scénario où le profit augmente. Volume quasi stable.",
        },
        "C": {
            "titre":    "Scénario C",
            "sous":     "Prix inchangés",
            "verdict":  "À éviter",
            "verdict_color": _WHITE,
            "verdict_bg":    _RED,
            "icone":    "❌",
            "message":  "Les coûts montent mais les prix restent fixes : profit chute de 20%.",
        },
    }

    def _metric_row(label, value_str, val_float):
        color = _color(val_float)
        arrow = "▲" if val_float > 0 else "▼"
        return html.Div([
            html.Span(label, style={"color": "#555", "fontSize": "12px", "flex": "1"}),
            html.Span(f"{arrow} {value_str}", style={
                "color": color, "fontWeight": "700", "fontSize": "13px",
            }),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "padding": "6px 0", "borderBottom": "1px solid #F0F0F0"})

    # ── Construire les 3 cartes ───────────────────────────────────────────────
    cards = []
    for scen_id, cfg in scenarios_config.items():
        if scen_id not in agg.index:
            continue
        row = agg.loc[scen_id]
        profit  = float(row["delta_profit_pct"])
        volume  = float(row["delta_volume_pct"])
        marge   = float(row["delta_marge_pts"])

        is_best = scen_id == "B"
        border  = f"3px solid {_GREEN}" if is_best else "2px solid #E8E8E8"
        shadow  = "0 4px 16px rgba(15,110,86,0.18)" if is_best else "0 2px 8px rgba(0,0,0,0.07)"

        card = html.Div([
            # Badge verdict
            html.Div(cfg["verdict"], style={
                "backgroundColor": cfg["verdict_bg"],
                "color": cfg["verdict_color"],
                "fontSize": "11px", "fontWeight": "700",
                "padding": "4px 12px", "borderRadius": "4px",
                "textAlign": "center", "marginBottom": "12px",
                "letterSpacing": "0.3px",
            }),
            # Titre
            html.H4(f"{cfg['icone']}  {cfg['titre']}", style={
                "color": _NAVY, "margin": "0 0 2px 0", "fontSize": "16px",
            }),
            html.P(cfg["sous"], style={
                "color": _GREY2, "fontSize": "12px", "margin": "0 0 14px 0",
            }),
            # Métriques
            _metric_row("Impact sur le profit",        _pct(profit),  profit),
            _metric_row("Impact sur le volume vendu",  _pct(volume),  volume),
            _metric_row("Impact sur la marge brute",   _pts(marge),   marge),
            # Message
            html.P(cfg["message"], style={
                "color": "#555", "fontSize": "12px",
                "margin": "12px 0 0 0", "lineHeight": "1.5",
                "fontStyle": "italic",
            }),
        ], style={
            "backgroundColor": "#FFFFFF",
            "border": border,
            "borderRadius": "10px",
            "boxShadow": shadow,
            "padding": "20px",
            "flex": "1",
            "minWidth": "220px",
            "transform": "scale(1.02)" if is_best else "scale(1)",
        })
        cards.append(card)

    # ── Graphique simple : profit uniquement ──────────────────────────────────
    scen_noms   = ["Scénario A\n+3%", "Scénario B\n+5%", "Scénario C\nInchangé"]
    profit_vals = [float(agg.loc[s]["delta_profit_pct"]) * 100 for s in ["A", "B", "C"]]
    bar_colors  = [_color(v / 100) for v in profit_vals]
    bar_texts   = [f"{v:+.1f}%" for v in profit_vals]

    fig_profit = go.Figure(go.Bar(
        x=scen_noms,
        y=profit_vals,
        marker_color=bar_colors,
        text=bar_texts,
        textposition="outside",
        textfont=dict(size=13, color=_NAVY),
        hovertemplate="<b>%{x}</b><br>Impact sur le profit : %{y:+.1f}%<extra></extra>",
    ))
    fig_profit.add_hline(y=0, line_color=_NAVY, line_width=1.5)
    # Annotation meilleur scénario
    fig_profit.add_annotation(
        x="Scénario B\n+5%", y=float(agg.loc["B"]["delta_profit_pct"]) * 100,
        text="★ Meilleur choix",
        showarrow=True, arrowhead=2, arrowcolor=_GREEN,
        font=dict(color=_GREEN, size=12, family="Inter, Arial"),
        yshift=20,
    )
    fig_profit.update_layout(
        title=dict(text="Quel impact sur votre profit selon le scénario choisi ?", font=dict(size=13)),
        yaxis_title="Variation du profit (%)",
        yaxis_ticksuffix="%",
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=60, r=20, t=55, b=55),
        height=300,
        showlegend=False,
        plot_bgcolor="#FAFAFA",
    )

    return html.Div([
        html.Div(cards, style={
            "display": "flex", "gap": "16px", "flexWrap": "wrap",
            "marginBottom": "20px",
        }),
        dcc.Graph(figure=fig_profit, config={"displayModeBar": False}),
    ])


# ════════════════════════════════════════════════════════════════
# PAGE PORTEFEUILLE PRODUITS
# ════════════════════════════════════════════════════════════════

def fig_bcg_matrix(raw: pd.DataFrame) -> go.Figure:
    """Classement des produits selon leur volume de ventes et leur rentabilité."""
    if raw is None or raw.empty:
        return _empty()

    sku_agg = (
        raw.groupby("sku_id")
        .agg(volume=("volume_vendu", "sum"), marge=("marge_brute_pct", "mean"), ca=("ca", "sum"))
        .reset_index()
    )

    vol_med   = sku_agg["volume"].median()
    marge_med = sku_agg["marge"].median()

    quadrant_cfg = {
        "Stars ★ — Forte vente, forte marge":       (_GREEN, lambda r: r["volume"] >= vol_med and r["marge"] >= marge_med),
        "Vaches à lait — Faible vente, forte marge": (_AMBER, lambda r: r["volume"] < vol_med  and r["marge"] >= marge_med),
        "Dilemmes — Forte vente, faible marge":      (_BLUE,  lambda r: r["volume"] >= vol_med and r["marge"] < marge_med),
        "Poids morts — Faible vente, faible marge":  (_RED,   lambda r: r["volume"] < vol_med  and r["marge"] < marge_med),
    }

    fig = go.Figure()
    for label, (color, cond) in quadrant_cfg.items():
        sub = sku_agg[sku_agg.apply(cond, axis=1)]
        if sub.empty:
            continue
        max_ca = sku_agg["ca"].max()
        fig.add_trace(go.Scatter(
            x=sub["marge"] * 100,
            y=sub["volume"],
            mode="markers+text",
            name=label,
            marker=dict(
                size=sub["ca"].apply(lambda v: max(10, min(30, v / max_ca * 28))),
                color=color, opacity=0.82,
                line=dict(color="white", width=1),
            ),
            text=sub["sku_id"].str.replace("SKU-", "", regex=False),
            textposition="top center",
            textfont=dict(size=9, color="#2C3E50"),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Marge brute : %{x:.1f}%<br>"
                "Volume vendu : %{y:,.0f} litres<extra></extra>"
            ),
        ))

    # Quadrant lines
    fig.add_vline(x=marge_med * 100, line_dash="dot", line_color="#BDC3C7", line_width=1.5)
    fig.add_hline(y=vol_med, line_dash="dot", line_color="#BDC3C7", line_width=1.5)

    fig.update_layout(
        title=dict(text="Carte des produits : volume vendu vs rentabilité", font=dict(size=14)),
        xaxis_title="Marge brute du produit (%)",
        yaxis_title="Volume total vendu (litres)",
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=65, r=20, t=65, b=55),
        height=460,
        legend=dict(orientation="h", y=-0.22, x=0, font=dict(size=10)),
        plot_bgcolor="#FAFAFA",
    )
    return fig


def fig_gap_skus(gap_sku_df: pd.DataFrame) -> go.Figure:
    """Fiabilité des prévisions de vente par produit.

    Métrique : % de mois où le produit a atteint ou dépassé sa cible (écart ≥ -5%).
    Un score de 100% = toujours dans les objectifs.
    Un score < 50% = ce produit manque sa cible un mois sur deux → action requise.
    """
    if gap_sku_df is None or gap_sku_df.empty:
        return _empty("Analyse d'écart non disponible — lancer d'abord run_m5.py")

    col_sku = "sku_code" if "sku_code" in gap_sku_df.columns else gap_sku_df.columns[0]

    # Filtrer sur volume_vendu si la colonne target existe
    df = gap_sku_df
    if "target" in gap_sku_df.columns:
        df = gap_sku_df[gap_sku_df["target"] == "volume_vendu"]
    if df.empty:
        df = gap_sku_df

    agg = (
        df.groupby(col_sku)
        .apply(lambda g: pd.Series({
            "hit_rate":       (g["gap_rel"] >= -0.05).mean() * 100,
            "pire_ecart":     g["gap_rel"].min() * 100,
            "meilleur_ecart": g["gap_rel"].max() * 100,
            "nb_mois":        len(g),
        }))
        .reset_index()
        .sort_values("hit_rate", ascending=True)
    )
    agg["nom"] = agg[col_sku].str.replace("SKU-", "", regex=False)

    colors = [
        _GREEN if r >= 70 else (_AMBER if r >= 50 else _RED)
        for r in agg["hit_rate"]
    ]

    fig = go.Figure(go.Bar(
        x=agg["hit_rate"],
        y=agg["nom"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.0f}%" for v in agg["hit_rate"]],
        textposition="outside",
        cliponaxis=False,
        customdata=agg[["pire_ecart", "meilleur_ecart", "nb_mois"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Mois dans cible : <b>%{x:.0f}%</b><br>"
            "Pire mois : %{customdata[0]:.1f}%<br>"
            "Meilleur mois : %{customdata[1]:.1f}%<br>"
            "Période analysée : %{customdata[2]:.0f} mois<extra></extra>"
        ),
    ))

    # Seuils de référence
    fig.add_vline(x=70, line_dash="dot", line_color=_GREEN, line_width=1.5,
                  annotation_text="Objectif 70%",
                  annotation_font_size=10, annotation_font_color=_GREEN,
                  annotation_position="top")
    fig.add_vline(x=50, line_dash="dot", line_color=_RED, line_width=1.5,
                  annotation_text="Seuil critique 50%",
                  annotation_font_size=10, annotation_font_color=_RED,
                  annotation_position="top")

    # Zone critique
    fig.add_vrect(
        x0=0, x1=50,
        fillcolor="rgba(153,60,29,0.04)",
        layer="below", line_width=0,
    )

    fig.update_xaxes(range=[0, 120], ticksuffix="%")

    fig.update_layout(
        title=dict(
            text=(
                "Fiabilité des prévisions par produit "
                "— % de mois où l'objectif de vente est atteint"
            ),
            font=dict(size=13),
        ),
        xaxis_title="% de mois dans la cible (écart ≥ −5%)",
        template=_TEMPLATE, font=_FONT,
        margin=dict(l=160, r=60, t=65, b=45),
        height=max(360, len(agg) * 28 + 120),
        showlegend=False,
        plot_bgcolor="#FAFAFA",
    )
    return fig
