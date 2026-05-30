"""Plotly figures for M3 — Pricing Simulation Engine."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Palette (cohérente M1/M2) ─────────────────────────────────────────────────
_C_A     = "#1A6B9A"   # bleu   — Scénario A (+3%)
_C_B     = "#E07B39"   # orange — Scénario B (+5%)
_C_C     = "#7F8C8D"   # gris   — Scénario C (inchangé)
_C_GREEN = "#27AE60"
_C_RED   = "#C0392B"
_C_AMBER = "#F39C12"

_SCENARIO_COLORS = {"A": _C_A, "B": _C_B, "C": _C_C}
_TEMPLATE = "plotly_white"
_FONT = dict(family="Inter, Arial, sans-serif", size=12, color="#2C3E50")


def fig_scenario_comparison(results_df: pd.DataFrame) -> go.Figure:
    """Graphique multi-métriques : A vs B vs C, par canal.

    3 sous-graphiques côte à côte : Δ Marge (pts) | Δ Volume (%) | Δ Profit (%)

    Données attendues (output de run_all_scenarios()) :
        canal | scenario | scenario_label | delta_marge_pts |
        delta_volume_pct | delta_profit_pct
    """
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["Δ Marge (points)", "Δ Volume (%)", "Δ Profit (%)"],
        shared_yaxes=True,
    )

    canaux = results_df["canal"].unique().tolist()

    for scenario_key in ["A", "B", "C"]:
        sub = results_df[results_df["scenario"] == scenario_key]
        label = sub["scenario_label"].iloc[0] if len(sub) > 0 else scenario_key
        color = _SCENARIO_COLORS[scenario_key]

        fig.add_trace(go.Bar(
            x=sub["delta_marge_pts"] * 100,
            y=sub["canal"],
            orientation="h",
            name=label,
            marker_color=color,
            legendgroup=scenario_key,
            hovertemplate=f"Scénario {label}<br>Canal: %{{y}}<br>Δ Marge: %{{x:+.2f}} pts<extra></extra>",
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            x=sub["delta_volume_pct"] * 100,
            y=sub["canal"],
            orientation="h",
            name=label,
            marker_color=color,
            legendgroup=scenario_key,
            showlegend=False,
            hovertemplate=f"Scénario {label}<br>Canal: %{{y}}<br>Δ Volume: %{{x:+.1f}}%<extra></extra>",
        ), row=1, col=2)

        fig.add_trace(go.Bar(
            x=sub["delta_profit_pct"] * 100,
            y=sub["canal"],
            orientation="h",
            name=label,
            marker_color=color,
            legendgroup=scenario_key,
            showlegend=False,
            hovertemplate=f"Scénario {label}<br>Canal: %{{y}}<br>Δ Profit: %{{x:+.1f}}%<extra></extra>",
        ), row=1, col=3)

    for col in [1, 2, 3]:
        fig.add_vline(x=0, line_dash="dash", line_color="#BDC3C7", line_width=1, row=1, col=col)

    fig.update_layout(
        title=dict(text="Comparaison Scénarios A / B / C — Impact par Canal", font=dict(size=15)),
        barmode="group",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=130, r=20, t=80, b=50),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.5),
    )
    return fig


def fig_pi_requirements(pi_df: pd.DataFrame) -> go.Figure:
    """Scatter : PI requis par SKU, coloré par urgence, taille = volume.

    Données attendues (output de compute_pi_recommendations()) :
        sku_id | canal | pi_requis | marge_sans_pi | urgence | volume_moy
    """
    _urgence_color = {
        "CRITIQUE": _C_RED,
        "ÉLEVÉE":   _C_AMBER,
        "MODÉRÉE":  _C_A,
        "FAIBLE":   _C_GREEN,
    }

    colors = [_urgence_color.get(u, _C_A) for u in pi_df["urgence"]]
    sizes  = (pi_df["volume_moy"] / pi_df["volume_moy"].max() * 25 + 6).round(0)

    fig = go.Figure(go.Scatter(
        x=pi_df["pi_requis"] * 100,
        y=pi_df["marge_sans_pi"] * 100,
        mode="markers",
        marker=dict(color=colors, size=sizes, opacity=0.8,
                    line=dict(color="white", width=1)),
        customdata=pi_df[["sku_id", "canal", "urgence", "marge_avant"]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Canal : %{customdata[1]}<br>"
            "PI requis : %{x:.1f}%<br>"
            "Marge sans PI : %{y:.1f}%<br>"
            "Marge actuelle : %{customdata[3]:.1%}<br>"
            "Urgence : %{customdata[2]}<extra></extra>"
        ),
    ))

    fig.add_hline(y=20, line_dash="dash", line_color=_C_RED,   line_width=1,
                  annotation_text="Seuil alerte 20%", annotation_position="right",
                  annotation_font_size=10)
    fig.add_vline(x=0,  line_dash="dash", line_color="#BDC3C7", line_width=1)

    fig.update_layout(
        title=dict(text="PI Requis par SKU × Canal (choc Brent)", font=dict(size=15)),
        xaxis_title="PI requis (%)",
        yaxis_title="Marge sans PI (%)",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=60, b=60),
    )
    return fig


def fig_monte_carlo(mc_df: pd.DataFrame) -> go.Figure:
    """Fan chart Monte Carlo : P5/P50/P95 de la marge par scénario pour chaque canal.

    Données attendues (output de run_monte_carlo()) :
        scenario | scenario_label | canal | marge_p5 | marge_p50 | marge_p95
    """
    canaux = mc_df["canal"].unique().tolist()
    n_canaux = len(canaux)

    fig = make_subplots(
        rows=1, cols=n_canaux,
        subplot_titles=canaux,
        shared_yaxes=True,
    )

    for col_idx, canal in enumerate(canaux, start=1):
        sub = mc_df[mc_df["canal"] == canal].sort_values("scenario")

        for _, row in sub.iterrows():
            color = _SCENARIO_COLORS.get(row["scenario"], _C_A)
            label = row["scenario_label"]
            x_pos = row["scenario"]

            # Barre P5→P95
            fig.add_trace(go.Box(
                x=[x_pos],
                lowerfence=[row["marge_p5"] * 100],
                q1=[row["marge_p50"] * 100],
                median=[row["marge_p50"] * 100],
                q3=[row["marge_p50"] * 100],
                upperfence=[row["marge_p95"] * 100],
                name=label,
                marker_color=color,
                legendgroup=row["scenario"],
                showlegend=(col_idx == 1),
                hovertemplate=(
                    f"Scénario {label}<br>"
                    "P5 : %{lowerfence:.1f}%<br>"
                    "P50: %{median:.1f}%<br>"
                    "P95: %{upperfence:.1f}%<extra></extra>"
                ),
            ), row=1, col=col_idx)

        fig.add_hline(y=20, line_dash="dash", line_color=_C_RED, line_width=1,
                      row=1, col=col_idx)

    fig.update_layout(
        title=dict(text="Intervalles de Confiance Marge — Monte Carlo P5/P50/P95", font=dict(size=15)),
        yaxis_title="Marge brute (%)",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=80, b=50),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.5),
        boxmode="group",
    )
    return fig


def fig_elasticity_impact(results_df: pd.DataFrame) -> go.Figure:
    """Tornado chart : quel canal perd le plus de volume selon le scénario ?

    Données attendues (output de run_all_scenarios()) :
        canal | scenario | scenario_label | delta_volume_pct | elasticite
    """
    # On garde B (PI +5%, scénario le plus impactant sur le volume)
    sub = results_df[results_df["scenario"] == "B"].sort_values("delta_volume_pct")

    colors = [_C_RED if v < -0.05 else _C_AMBER if v < 0 else _C_GREEN
              for v in sub["delta_volume_pct"]]

    fig = go.Figure(go.Bar(
        x=sub["delta_volume_pct"] * 100,
        y=sub["canal"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in sub["delta_volume_pct"] * 100],
        textposition="outside",
        customdata=sub["elasticite"],
        hovertemplate=(
            "Canal : %{y}<br>"
            "Δ Volume : %{x:+.1f}%<br>"
            "Élasticité : %{customdata:.2f}<extra></extra>"
        ),
    ))

    fig.add_vline(x=0, line_dash="dash", line_color="#BDC3C7", line_width=1)

    fig.update_layout(
        title=dict(text="Impact Volume par Canal — Scénario B (PI +5%)", font=dict(size=15)),
        xaxis_title="Variation volume (%)",
        yaxis_title="Canal",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=130, r=80, t=60, b=50),
    )
    return fig


def build_all_figures(
    results_df: pd.DataFrame,
    pi_df: pd.DataFrame,
    mc_df: pd.DataFrame,
) -> dict[str, go.Figure]:
    """Construit les 4 figures M3 et les retourne dans un dict nommé."""
    return {
        "scenario_comparison": fig_scenario_comparison(results_df),
        "pi_requirements":     fig_pi_requirements(pi_df),
        "monte_carlo":         fig_monte_carlo(mc_df),
        "elasticity_impact":   fig_elasticity_impact(results_df),
    }
