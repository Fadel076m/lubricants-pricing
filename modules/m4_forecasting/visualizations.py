"""Plotly figures for M4 — Forecasting."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_C_ACTUAL   = "#1A6B9A"
_C_PROPHET  = "#27AE60"
_C_XGB      = "#E07B39"
_C_LSTM     = "#9B59B6"
_C_CI       = "rgba(39, 174, 96, 0.15)"
_C_RED      = "#C0392B"
_C_GREY     = "#7F8C8D"

_MODEL_COLORS = {"prophet": _C_PROPHET, "xgboost": _C_XGB, "lstm": _C_LSTM}
_TEMPLATE = "plotly_white"
_FONT = dict(family="Inter, Arial, sans-serif", size=12, color="#2C3E50")

_TARGET_LABELS = {
    "volume_vendu":    "Volume vendu (L/mois)",
    "nsp":             "NSP moyen (devise locale/L)",
    "marge_brute_pct": "Marge brute (%)",
}


def fig_forecast_vs_actual(
    df_monthly: pd.DataFrame,
    forecasts_df: pd.DataFrame,
    target: str,
) -> go.Figure:
    """Line chart : historique réel + prévisions 30/60/90j par modèle.

    Données attendues :
        df_monthly  : output de build_monthly_aggregates
        forecasts_df: output de run_forecast_pipeline['forecasts']
        target      : 'volume_vendu' | 'nsp' | 'marge_brute_pct'
    """
    fig = go.Figure()

    # Historique réel
    fig.add_trace(go.Scatter(
        x=df_monthly["date"],
        y=df_monthly[target] * (100 if target == "marge_brute_pct" else 1),
        name="Réel (historique)",
        mode="lines+markers",
        line=dict(color=_C_ACTUAL, width=2),
        marker=dict(size=4),
        hovertemplate="%{x|%b %Y}<br>Réel : %{y:,.2f}<extra></extra>",
    ))

    # Forecasts par modèle
    fc_target = forecasts_df[forecasts_df["target"] == target]
    for model_name in fc_target["best_model"].unique():
        fc_model = fc_target[fc_target["best_model"] == model_name]
        color = _MODEL_COLORS.get(model_name, _C_GREY)

        # Ligne de continuité (dernier point réel → premier forecast)
        last_real = df_monthly.tail(1)
        bridge_x  = [last_real["date"].iloc[0]] + list(fc_model["ds"])
        bridge_y  = [last_real[target].iloc[0] * (100 if target == "marge_brute_pct" else 1)] + \
                    list(fc_model["yhat"] * (100 if target == "marge_brute_pct" else 1))

        fig.add_trace(go.Scatter(
            x=bridge_x,
            y=bridge_y,
            name=f"Forecast {model_name}",
            mode="lines+markers",
            line=dict(color=color, width=2, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
            hovertemplate="%{x|%b %Y}<br>Forecast : %{y:,.2f}<extra></extra>",
        ))

    # Ligne verticale séparant historique et forecast
    last_date = df_monthly["date"].iloc[-1]
    fig.add_vline(
        x=last_date.timestamp() * 1000,
        line_dash="dot", line_color=_C_GREY, line_width=1,
        annotation_text="Début forecast", annotation_position="top left",
        annotation_font_size=10,
    )

    fig.update_layout(
        title=dict(
            text=f"Forecast — {_TARGET_LABELS.get(target, target)}",
            font=dict(size=15)
        ),
        xaxis_title="Mois",
        yaxis_title=_TARGET_LABELS.get(target, target),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=70, r=20, t=70, b=50),
        hovermode="x unified",
    )
    return fig


def fig_model_metrics(metrics_df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart : MAPE par modèle × cible.

    Données attendues (output de compare_models()) :
        model | target | MAPE | RMSE | MAE
    """
    targets = metrics_df["target"].unique().tolist()
    n = len(targets)

    fig = make_subplots(rows=1, cols=n, subplot_titles=targets, shared_yaxes=True)

    for col_idx, target in enumerate(targets, start=1):
        sub = metrics_df[metrics_df["target"] == target].dropna(subset=["MAPE"])

        for _, row in sub.iterrows():
            color = _MODEL_COLORS.get(row["model"], _C_GREY)
            fig.add_trace(go.Bar(
                x=[row["model"]],
                y=[row["MAPE"]],
                name=row["model"],
                marker_color=color,
                legendgroup=row["model"],
                showlegend=(col_idx == 1),
                text=[f"{row['MAPE']:.2f}%"],
                textposition="outside",
                hovertemplate=(
                    f"Modèle : {row['model']}<br>"
                    f"MAPE : {row['MAPE']:.2f}%<br>"
                    f"RMSE : {row['RMSE']:.2f}<extra></extra>"
                ),
            ), row=1, col=col_idx)

        # Ligne cible MAPE
        target_mape = 8 if target == "volume_vendu" else 5
        fig.add_hline(
            y=target_mape,
            line_dash="dash", line_color=_C_RED, line_width=1,
            annotation_text=f"Cible {target_mape}%",
            annotation_font_size=9,
            row=1, col=col_idx,
        )

    fig.update_layout(
        title=dict(text="Comparaison Modèles — MAPE par Cible", font=dict(size=15)),
        yaxis_title="MAPE (%)",
        barmode="group",
        template=_TEMPLATE,
        font=_FONT,
        margin=dict(l=60, r=20, t=80, b=50),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.5),
    )
    return fig


def build_all_figures(
    df_monthly: pd.DataFrame,
    forecasts_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
) -> dict[str, go.Figure]:
    """Construit les figures M4 : une par cible + comparaison modèles."""
    figs: dict[str, go.Figure] = {}
    for target in ["volume_vendu", "nsp", "marge_brute_pct"]:
        figs[f"forecast_{target}"] = fig_forecast_vs_actual(df_monthly, forecasts_df, target)
    figs["model_metrics"] = fig_model_metrics(metrics_df)
    return figs
