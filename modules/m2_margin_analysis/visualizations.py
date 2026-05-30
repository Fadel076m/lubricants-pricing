"""Plotly figures for M2 — Margin Analysis."""

import pandas as pd
import plotly.graph_objects as go

# ── Palette (cohérente avec M1) ───────────────────────────────────────────────
_C_GREEN  = "#27AE60"
_C_AMBER  = "#F39C12"
_C_RED    = "#C0392B"
_C_BLUE   = "#1A6B9A"
_C_ORANGE = "#E07B39"
_C_GREY   = "#7F8C8D"

_COGS_COLORS = {
    "Huile de base": "#1A3A5C",
    "Additifs":      "#2E86AB",
    "Transport":     "#E07B39",
    "Packaging":     "#95A5A6",
    "Stockage":      "#BDC3C7",
}

_TEMPLATE = "plotly_white"
_FONT = dict(family="Inter, Arial, sans-serif", size=12, color="#2C3E50")


def fig_waterfall_cogs(breakdown_df: pd.DataFrame) -> go.Figure:
    """Waterfall chart : décomposition COGS global en 5 postes.

    Montre visuellement quelle part de chaque poste compose le COGS total.

    Données attendues (output de compute_cogs_breakdown() sans group_by) :
        poste | label | valeur_moyenne | part_pct_cogs
    """
    df = breakdown_df.sort_values("valeur_moyenne", ascending=False)

    total = df["valeur_moyenne"].sum()

    labels = list(df["label"]) + ["COGS Total"]
    values = list(df["valeur_moyenne"]) + [total]
    measure = ["relative"] * len(df) + ["total"]
    colors = [_COGS_COLORS.get(lbl, _C_GREY) for lbl in df["label"]] + [_C_BLUE]

    text = [f"{row['part_pct_cogs']:.1%}" for _, row in df.iterrows()] + [
        f"{total:,.0f}"
    ]

    fig = go.Figure(go.Waterfall(
        name="COGS",
        orientation="v",
        measure=measure,
        x=labels,
        y=values,
        text=text,
        textposition="outside",
        connector=dict(line=dict(color=_C_GREY, width=1, dash="dot")),
        increasing=dict(marker_color=_C_BLUE),
        totals=dict(marker_color=_C_BLUE),
        decreasing=dict(marker_color=_C_RED),
    ))

    fig.update_layout(
        title=dict(text="Décomposition COGS — 5 Postes", font=dict(size=15)),
        xaxis_title="Poste COGS",
        yaxis_title="Coût moyen (monnaie locale/L)",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=60, b=50),
        showlegend=False,
    )
    return fig


def fig_margin_heatmap_sku_canal(pivot_df: pd.DataFrame) -> go.Figure:
    """Heatmap marge brute % : SKUs (lignes) × Canaux (colonnes).

    Permet d'identifier d'un coup d'oeil les combinaisons critiques.
    Rouge = marge < 20%, Vert = marge ≥ 30%.

    Données attendues (output de compute_margin_pivot_sku_canal().reset_index()) :
        sku_id | B2B Industrie | B2B OEM | B2C GMS | ...
    """
    canaux = [c for c in pivot_df.columns if c != "sku_id"]
    z = pivot_df[canaux].values * 100

    text = [[f"{v:.1f}%" for v in row] for row in z]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=canaux,
        y=pivot_df["sku_id"].tolist(),
        text=text,
        texttemplate="%{text}",
        colorscale=[
            [0.0,  "#C0392B"],  # rouge  < 20%
            [0.2,  "#E74C3C"],
            [0.3,  "#F39C12"],  # ambre  20-30%
            [0.4,  "#F9E79F"],
            [0.5,  "#EAFAF1"],
            [1.0,  "#27AE60"],  # vert   ≥ 30%
        ],
        zmin=0,
        zmax=50,
        colorbar=dict(
            title="Marge brute %",
            tickformat=".0f",
            ticksuffix="%",
        ),
        hovertemplate="SKU: %{y}<br>Canal: %{x}<br>Marge: %{text}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="Marge Brute % par SKU × Canal", font=dict(size=15)),
        xaxis_title="Canal",
        yaxis_title="SKU",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=140, r=20, t=60, b=80),
        height=max(400, len(pivot_df) * 22),
    )
    return fig


def fig_margin_by_channel(channel_df: pd.DataFrame) -> go.Figure:
    """Bar chart horizontal : marge brute % moyenne par canal.

    Couleur selon la zone : rouge < 20%, ambre 20-30%, vert ≥ 30%.

    Données attendues (output de compute_margin_by_channel()) :
        canal | marge_brute_pct_moy | contribution_ca_pct | ...
    """
    df = channel_df.sort_values("marge_brute_pct_moy")

    def _color(m: float) -> str:
        if m < 0.20:
            return _C_RED
        if m < 0.30:
            return _C_AMBER
        return _C_GREEN

    colors = [_color(m) for m in df["marge_brute_pct_moy"]]

    fig = go.Figure(go.Bar(
        x=df["marge_brute_pct_moy"] * 100,
        y=df["canal"],
        orientation="h",
        marker_color=colors,
        text=[f"{m:.1%}" for m in df["marge_brute_pct_moy"]],
        textposition="outside",
        customdata=df["contribution_ca_pct"],
        hovertemplate=(
            "Canal : %{y}<br>"
            "Marge : %{x:.1f}%<br>"
            "Part CA : %{customdata:.1%}<extra></extra>"
        ),
    ))

    fig.add_vline(x=20, line_dash="dash", line_color=_C_RED,   line_width=1,
                  annotation_text="Seuil alerte 20%", annotation_position="top right",
                  annotation_font_size=10)
    fig.add_vline(x=30, line_dash="dash", line_color=_C_GREEN, line_width=1,
                  annotation_text="Seuil sain 30%", annotation_position="top right",
                  annotation_font_size=10)

    fig.update_layout(
        title=dict(text="Marge Brute % par Canal", font=dict(size=15)),
        xaxis_title="Marge brute moyenne (%)",
        yaxis_title="Canal",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=130, r=80, t=60, b=50),
        xaxis=dict(range=[0, max(df["marge_brute_pct_moy"]) * 120]),
    )
    return fig


def fig_sku_alerts(alerts_df: pd.DataFrame) -> go.Figure:
    """Scatter plot des SKUs en alerte : marge moyenne vs % transactions rouge.

    Quadrant danger = marge basse + beaucoup de transactions rouge.

    Données attendues (output de get_sku_alerts()) :
        sku_id | produit | marge_pct_moy | pct_rouge | statut_dominant | ...
    """
    def _color(s: str) -> str:
        return {
            "ROUGE": _C_RED,
            "AMBRE": _C_AMBER,
        }.get(s, _C_GREEN)

    colors = [_color(s) for s in alerts_df["statut_dominant"]]

    fig = go.Figure(go.Scatter(
        x=alerts_df["marge_pct_moy"] * 100,
        y=alerts_df["pct_rouge"] * 100,
        mode="markers+text",
        marker=dict(color=colors, size=12, opacity=0.85,
                    line=dict(color="white", width=1)),
        text=alerts_df["sku_id"],
        textposition="top center",
        textfont=dict(size=9),
        customdata=alerts_df[["produit", "canal_plus_risque", "statut_dominant"]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Marge moy : %{x:.1f}%<br>"
            "% transac. rouge : %{y:.1f}%<br>"
            "Canal risque : %{customdata[1]}<br>"
            "Statut : %{customdata[2]}<extra></extra>"
        ),
    ))

    fig.add_vline(x=20, line_dash="dash", line_color=_C_RED,  line_width=1)
    fig.add_hline(y=50, line_dash="dash", line_color=_C_GREY, line_width=1,
                  annotation_text="50% des ventes en rouge",
                  annotation_position="right", annotation_font_size=10)

    fig.update_layout(
        title=dict(text="SKUs en Alerte — Marge vs Fréquence Rouge", font=dict(size=15)),
        xaxis_title="Marge brute moyenne (%)",
        yaxis_title="% transactions en zone rouge",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=60, b=60),
    )
    return fig


def fig_brent_sensitivity(sensitivity_df: pd.DataFrame, shock_pct: float = 0.10) -> go.Figure:
    """Bar chart groupé : marge actuelle vs marge après choc Brent, par canal.

    Données attendues (output de compute_brent_sensitivity()) :
        canal | marge_actuelle_pct | marge_choc_pct | delta_pts | ...
    """
    df = sensitivity_df.sort_values("marge_actuelle_pct")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["canal"],
        y=df["marge_actuelle_pct"] * 100,
        name="Marge actuelle",
        marker_color=_C_BLUE,
        hovertemplate="Canal : %{x}<br>Marge actuelle : %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=df["canal"],
        y=df["marge_choc_pct"] * 100,
        name=f"Marge après choc Brent +{shock_pct:.0%}",
        marker_color=_C_RED,
        hovertemplate="Canal : %{x}<br>Marge choc : %{y:.1f}%<extra></extra>",
    ))

    # Annotations delta
    for _, row in df.iterrows():
        fig.add_annotation(
            x=row["canal"],
            y=row["marge_choc_pct"] * 100 - 1.5,
            text=f"{row['delta_pts']*100:+.1f} pts",
            showarrow=False,
            font=dict(size=10, color="white"),
        )

    fig.add_hline(y=20, line_dash="dash", line_color=_C_RED, line_width=1,
                  annotation_text="Seuil alerte 20%", annotation_position="right",
                  annotation_font_size=10)

    fig.update_layout(
        title=dict(
            text=f"Sensibilité Marge au Choc Brent ({shock_pct:+.0%})",
            font=dict(size=15)
        ),
        barmode="group",
        xaxis_title="Canal",
        yaxis_title="Marge brute (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=80, b=50),
    )
    return fig


def build_all_figures(
    breakdown_df: pd.DataFrame,
    channel_df: pd.DataFrame,
    pivot_df: pd.DataFrame,
    alerts_df: pd.DataFrame,
    sensitivity_df: pd.DataFrame,
    brent_shock_pct: float = 0.10,
) -> dict[str, go.Figure]:
    """Construit les 5 figures M2 et les retourne dans un dict nommé."""
    return {
        "waterfall_cogs":        fig_waterfall_cogs(breakdown_df),
        "margin_by_channel":     fig_margin_by_channel(channel_df),
        "margin_heatmap":        fig_margin_heatmap_sku_canal(pivot_df),
        "sku_alerts":            fig_sku_alerts(alerts_df),
        "brent_sensitivity":     fig_brent_sensitivity(sensitivity_df, brent_shock_pct),
    }
