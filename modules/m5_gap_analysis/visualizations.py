"""Plotly figures for M5 — Gap Analysis."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .gap_engine import STATUS_CRITIQUE, STATUS_DEFAV, STATUS_IN_TARGET, STATUS_FAVORABLE

_TEMPLATE = "plotly_white"
_FONT = dict(family="Inter, Arial, sans-serif", size=12, color="#2C3E50")

_STATUS_COLORS = {
    STATUS_FAVORABLE:  "#27AE60",
    STATUS_IN_TARGET:  "#2980B9",
    STATUS_DEFAV:      "#E07B39",
    STATUS_CRITIQUE:   "#C0392B",
}


def fig_gap_global(gap_global_df: pd.DataFrame) -> go.Figure:
    """Bar chart horizontal : gap % par cible (volume / NSP / marge)."""
    if gap_global_df.empty:
        return go.Figure()

    df = gap_global_df.copy()
    df["gap_pct"] = df["gap_rel"] * 100
    df["color"]   = df["statut_gap"].map(_STATUS_COLORS).fillna("#7F8C8D")
    df["label"]   = df["gap_pct"].apply(lambda v: f"{v:+.1f}%")

    fig = go.Figure(go.Bar(
        x=df["gap_pct"],
        y=df["target"],
        orientation="h",
        marker_color=df["color"],
        text=df["label"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Gap : %{x:.1f}%<extra></extra>",
    ))

    fig.add_vline(x=0, line_color="#2C3E50", line_width=1)
    fig.add_vline(x=5, line_dash="dash", line_color=_STATUS_COLORS[STATUS_FAVORABLE],
                  line_width=1, annotation_text="+5%", annotation_font_size=9)
    fig.add_vline(x=-5, line_dash="dash", line_color=_STATUS_COLORS[STATUS_DEFAV],
                  line_width=1, annotation_text="-5%", annotation_font_size=9)
    fig.add_vline(x=-10, line_dash="dash", line_color=_STATUS_COLORS[STATUS_CRITIQUE],
                  line_width=1, annotation_text="-10%", annotation_font_size=9)

    fig.update_layout(
        title=dict(text="Gap Global — Réel vs Forecast (horizon 30j)", font=dict(size=15)),
        xaxis_title="Gap (%)",
        yaxis_title="",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=160, r=80, t=60, b=50),
        height=280,
    )
    return fig


def fig_gap_by_month(gap_month_df: pd.DataFrame, target: str = "volume_vendu") -> go.Figure:
    """Line chart : gap % mensuel pour une cible donnée (30/60/90j)."""
    if gap_month_df.empty:
        return go.Figure()

    df = gap_month_df[gap_month_df["target"] == target].copy()
    if df.empty:
        return go.Figure()

    df["gap_pct"] = df["gap_rel"] * 100

    fig = go.Figure()

    for horizon in sorted(df["horizon_days"].unique()):
        sub = df[df["horizon_days"] == horizon].sort_values("date")
        fig.add_trace(go.Scatter(
            x=sub["date"],
            y=sub["gap_pct"],
            name=f"Horizon {horizon}j",
            mode="lines+markers",
            hovertemplate="%{x|%b %Y}<br>Gap : %{y:+.1f}%<extra></extra>",
        ))

    # Bandes de seuil
    fig.add_hrect(y0=5,  y1=30,  fillcolor="#EAFAF1", opacity=0.25, layer="below", line_width=0)
    fig.add_hrect(y0=-5, y1=5,   fillcolor="#EBF5FB", opacity=0.25, layer="below", line_width=0)
    fig.add_hrect(y0=-10,y1=-5,  fillcolor="#FEF9E7", opacity=0.30, layer="below", line_width=0)
    fig.add_hrect(y0=-30,y1=-10, fillcolor="#FDEDEC", opacity=0.30, layer="below", line_width=0)
    fig.add_hline(y=0, line_color="#2C3E50", line_width=1)

    fig.update_layout(
        title=dict(text=f"Gap Mensuel — {target.replace('_',' ').title()}", font=dict(size=15)),
        xaxis_title="Mois",
        yaxis_title="Gap (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=70, b=50),
    )
    return fig


def fig_gap_heatmap(gap_canal_df: pd.DataFrame, target: str = "volume_vendu") -> go.Figure:
    """Heatmap : gap % par canal × mois."""
    if gap_canal_df.empty:
        return go.Figure()

    df = gap_canal_df[gap_canal_df["target"] == target].copy()
    if df.empty or "canal" not in df.columns:
        return go.Figure()

    df["gap_pct"] = df["gap_rel"] * 100
    pivot = df.pivot_table(index="canal", columns="date", values="gap_pct", aggfunc="mean")

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c)[:7] for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[
            [0.0,  "#C0392B"],
            [0.35, "#E07B39"],
            [0.50, "#2980B9"],
            [0.75, "#27AE60"],
            [1.0,  "#1E8449"],
        ],
        zmid=0,
        text=[[f"{v:+.1f}%" if not pd.isna(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont_size=10,
        hovertemplate="Canal : %{y}<br>Mois : %{x}<br>Gap : %{z:+.1f}%<extra></extra>",
        colorbar=dict(title="Gap %", ticksuffix="%"),
    ))

    fig.update_layout(
        title=dict(text=f"Gap par Canal × Mois — {target.replace('_',' ').title()}", font=dict(size=15)),
        xaxis_title="Mois",
        yaxis_title="",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=130, r=20, t=70, b=60),
        height=320,
    )
    return fig


def fig_gap_waterfall(gap_global_df: pd.DataFrame) -> go.Figure:
    """Waterfall : contribution de chaque cible au gap global normalisé."""
    if gap_global_df.empty:
        return go.Figure()

    df = gap_global_df.copy()
    df["gap_pct"] = df["gap_rel"] * 100

    measures = ["relative"] * len(df) + ["total"]
    x_labels = list(df["target"]) + ["Total"]
    y_values = list(df["gap_pct"]) + [df["gap_pct"].mean()]

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=x_labels,
        y=y_values,
        text=[f"{v:+.1f}%" for v in y_values],
        textposition="outside",
        increasing_marker_color=_STATUS_COLORS[STATUS_FAVORABLE],
        decreasing_marker_color=_STATUS_COLORS[STATUS_CRITIQUE],
        totals_marker_color="#1A6B9A",
        connector=dict(line=dict(color="#BDC3C7", width=1, dash="dot")),
        hovertemplate="%{x}<br>Gap : %{y:+.1f}%<extra></extra>",
    ))

    fig.add_hline(y=0, line_color="#2C3E50", line_width=1)

    fig.update_layout(
        title=dict(text="Contribution au Gap Global par Cible", font=dict(size=15)),
        yaxis_title="Gap (%)",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=70, b=50),
        height=360,
        showlegend=False,
    )
    return fig


def build_all_figures(
    gap_global_df: pd.DataFrame,
    gap_month_df: pd.DataFrame,
    gap_canal_df: pd.DataFrame,
) -> dict[str, go.Figure]:
    """Construit les 5 figures M5."""
    figs: dict[str, go.Figure] = {}
    figs["gap_global"]          = fig_gap_global(gap_global_df)
    figs["gap_waterfall"]       = fig_gap_waterfall(gap_global_df)
    figs["gap_monthly_volume"]  = fig_gap_by_month(gap_month_df, "volume_vendu")
    figs["gap_monthly_nsp"]     = fig_gap_by_month(gap_month_df, "nsp")
    figs["gap_heatmap_canal"]   = fig_gap_heatmap(gap_canal_df,  "volume_vendu")
    return figs
