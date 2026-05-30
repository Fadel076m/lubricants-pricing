"""Plotly figures for M1 — Market & Pricing Insights."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Palette ──────────────────────────────────────────────────────────────────
_C_NSP  = "#1A6B9A"   # bleu  — notre prix
_C_CONC = "#E07B39"   # orange — concurrent
_C_POS  = "#27AE60"   # vert  — favorable (on est moins cher)
_C_NEG  = "#C0392B"   # rouge — défavorable (on est plus cher)
_C_NEUT = "#7F8C8D"   # gris  — neutre

_TEMPLATE = "plotly_white"
_FONT = dict(family="Inter, Arial, sans-serif", size=12, color="#2C3E50")


def fig_price_evolution(evolution_df: pd.DataFrame) -> go.Figure:
    """Line chart : NSP moyen vs Prix Concurrent moyen, mois par mois.

    Données attendues (output de compute_price_evolution) :
        date | nsp | prix_concurrent | ecart_pct
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=evolution_df["date"],
        y=evolution_df["nsp"],
        name="NSP (notre prix)",
        mode="lines+markers",
        line=dict(color=_C_NSP, width=2),
        marker=dict(size=5),
        hovertemplate="%{x|%b %Y}<br>NSP : %{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=evolution_df["date"],
        y=evolution_df["prix_concurrent"],
        name="Prix concurrent",
        mode="lines+markers",
        line=dict(color=_C_CONC, width=2, dash="dot"),
        marker=dict(size=5),
        hovertemplate="%{x|%b %Y}<br>Concurrent : %{y:,.0f}<extra></extra>",
    ))

    # Zone de remplissage entre les deux courbes
    fig.add_trace(go.Scatter(
        x=pd.concat([evolution_df["date"], evolution_df["date"][::-1]]),
        y=pd.concat([evolution_df["nsp"], evolution_df["prix_concurrent"][::-1]]),
        fill="toself",
        fillcolor="rgba(26, 107, 154, 0.08)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(text="Évolution NSP vs Prix Concurrent", font=dict(size=15)),
        xaxis_title="Mois",
        yaxis_title="Prix moyen (monnaie locale)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=60, b=50),
        hovermode="x unified",
    )
    return fig


def fig_channel_benchmark(channel_df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart : NSP moyen vs Prix Concurrent moyen par canal.

    Données attendues (output de compute_channel_benchmark) :
        canal | nsp_moyen | prix_conc_moyen | indice_conc_moyen | ecart_absolu | ecart_pct
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=channel_df["canal"],
        y=channel_df["nsp_moyen"],
        name="NSP moyen",
        marker_color=_C_NSP,
        hovertemplate="Canal : %{x}<br>NSP : %{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=channel_df["canal"],
        y=channel_df["prix_conc_moyen"],
        name="Prix concurrent moyen",
        marker_color=_C_CONC,
        hovertemplate="Canal : %{x}<br>Concurrent : %{y:,.0f}<extra></extra>",
    ))

    # Annotation écart % au-dessus de chaque groupe
    for _, row in channel_df.iterrows():
        color = _C_NEG if row["ecart_pct"] > 0 else _C_POS
        sign = "+" if row["ecart_pct"] > 0 else ""
        fig.add_annotation(
            x=row["canal"],
            y=max(row["nsp_moyen"], row["prix_conc_moyen"]) * 1.04,
            text=f"{sign}{row['ecart_pct']:.1%}",
            showarrow=False,
            font=dict(size=11, color=color, family="Inter, Arial, sans-serif"),
        )

    fig.update_layout(
        title=dict(text="Benchmark Pricing par Canal", font=dict(size=15)),
        barmode="group",
        xaxis_title="Canal",
        yaxis_title="Prix moyen (monnaie locale)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=80, b=50),
    )
    return fig


def fig_regional_heatmap(region_pivot_df: pd.DataFrame) -> go.Figure:
    """Heatmap : écart % NSP vs Concurrent par Région × Famille.

    Rouge = on est plus cher que le concurrent.
    Vert  = on est moins cher que le concurrent.

    Données attendues (output de compute_regional_positioning.reset_index()) :
        region | Famille1 | Famille2 | ...
    """
    regions = region_pivot_df["region"].tolist()
    familles = [c for c in region_pivot_df.columns if c != "region"]
    z = region_pivot_df[familles].values * 100  # en pourcentage

    text = [[f"{v:+.1f}%" for v in row] for row in z]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=familles,
        y=regions,
        text=text,
        texttemplate="%{text}",
        colorscale=[
            [0.0,  "#27AE60"],  # vert foncé (on est bien moins cher)
            [0.45, "#D5F5E3"],  # vert clair
            [0.5,  "#FFFFFF"],  # neutre
            [0.55, "#FDECEA"],  # rouge clair
            [1.0,  "#C0392B"],  # rouge foncé (on est bien plus cher)
        ],
        zmid=0,
        colorbar=dict(
            title="Écart vs concurrent",
            tickformat="+.0f",
            ticksuffix="%",
        ),
        hovertemplate="Région : %{y}<br>Famille : %{x}<br>Écart : %{text}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="Positionnement Prix par Région & Famille", font=dict(size=15)),
        xaxis_title="Famille de produit",
        yaxis_title="Région",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=110, r=20, t=60, b=90),
    )
    return fig


def fig_price_elasticity(elasticity_df: pd.DataFrame) -> go.Figure:
    """Bar chart horizontal : élasticité-prix par canal.

    Rouge = élasticité forte (|e| ≥ 1) → très sensible au prix.
    Vert  = élasticité faible (|e| < 1) → peu sensible.

    Données attendues (output de compute_price_elasticity) :
        canal | elasticite
    """
    df = elasticity_df.sort_values("elasticite")
    colors = [_C_NEG if abs(e) >= 1 else _C_POS for e in df["elasticite"]]

    fig = go.Figure(go.Bar(
        x=df["elasticite"],
        y=df["canal"],
        orientation="h",
        marker_color=colors,
        text=[f"{e:+.2f}" for e in df["elasticite"]],
        textposition="outside",
        hovertemplate="Canal : %{y}<br>Élasticité : %{x:.2f}<extra></extra>",
    ))

    fig.add_vline(x=0,  line_dash="dash", line_color=_C_NEUT, line_width=1,
                  annotation_text="0", annotation_position="top",
                  annotation_font_size=10)
    fig.add_vline(x=-1, line_dash="dash", line_color=_C_NEUT, line_width=1,
                  annotation_text="-1", annotation_position="top",
                  annotation_font_size=10)

    fig.update_layout(
        title=dict(text="Élasticité-Prix par Canal (modèle log-log)", font=dict(size=15)),
        xaxis_title="Coefficient d'élasticité",
        yaxis_title="Canal",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=120, r=70, t=60, b=50),
        xaxis=dict(zeroline=True, zerolinecolor=_C_NEUT),
    )
    return fig


def fig_brent_cogs_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter : Brent (USD/baril) vs Coût Huile Base, agrégé par mois + droite OLS.

    Données attendues : DataFrame brut des transactions (24 colonnes).
    """
    monthly = (
        df.groupby("date")[["prix_brent_usd", "cout_huile_base"]]
        .mean()
        .reset_index()
    )

    x_vals = monthly["prix_brent_usd"].values
    y_vals = monthly["cout_huile_base"].values

    coeffs = np.polyfit(x_vals, y_vals, 1)
    x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
    y_line = np.polyval(coeffs, x_line)

    y_pred = np.polyval(coeffs, x_vals)
    ss_res = np.sum((y_vals - y_pred) ** 2)
    ss_tot = np.sum((y_vals - y_vals.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=monthly["prix_brent_usd"],
        y=monthly["cout_huile_base"],
        mode="markers",
        marker=dict(color=_C_NSP, size=8, opacity=0.8),
        name="Données mensuelles",
        customdata=monthly["date"],
        hovertemplate="%{customdata|%b %Y}<br>Brent : %{x:.1f} USD<br>Coût huile base : %{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=x_line,
        y=y_line,
        mode="lines",
        line=dict(color=_C_CONC, width=2, dash="dash"),
        name=f"Régression OLS (R²={r2:.2f})",
        hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(
            text=f"Corrélation Brent vs Coût Huile Base — R² = {r2:.2f}",
            font=dict(size=15),
        ),
        xaxis_title="Prix Brent (USD/baril)",
        yaxis_title="Coût huile base moyen (monnaie locale)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=80, r=20, t=70, b=60),
    )
    return fig


def build_all_figures(
    evolution_df: pd.DataFrame,
    channel_df: pd.DataFrame,
    region_pivot_df: pd.DataFrame,
    elasticity_df: pd.DataFrame,
    raw_df: pd.DataFrame,
) -> dict[str, go.Figure]:
    """Construit les 5 figures M1 et les retourne dans un dict nommé.

    Usage dans le Dash :
        figs = build_all_figures(...)
        dcc.Graph(figure=figs["price_evolution"])
    """
    return {
        "price_evolution":    fig_price_evolution(evolution_df),
        "channel_benchmark":  fig_channel_benchmark(channel_df),
        "regional_heatmap":   fig_regional_heatmap(region_pivot_df),
        "price_elasticity":   fig_price_elasticity(elasticity_df),
        "brent_cogs_scatter": fig_brent_cogs_scatter(raw_df),
    }
