"""Model comparison with MLflow logging — M4 Forecasting.

Pourquoi ce fichier ?
    Un Pricing Manager présente ses prévisions à la direction avec une
    justification de la méthode choisie. Ce module compare objectivement
    les 3 modèles (MAPE, RMSE, MAE) et sélectionne le meilleur
    automatiquement — tout en loggant dans MLflow pour la traçabilité.
"""

import pandas as pd
from loguru import logger

from .prophet_model import evaluate_prophet
from .xgboost_model import evaluate_xgboost
from .lstm_model import evaluate_lstm, TF_AVAILABLE

try:
    import mlflow
    _MLFLOW_AVAILABLE = True
except ImportError:
    _MLFLOW_AVAILABLE = False
    logger.warning("MLflow non disponible — tracking désactivé")

FORECAST_TARGETS = ["volume_vendu", "nsp", "marge_brute_pct"]


def compare_models(
    df_monthly: pd.DataFrame,
    targets: list[str] = FORECAST_TARGETS,
    n_test: int = 6,
) -> pd.DataFrame:
    """Walk-forward evaluation for Prophet / XGBoost / LSTM on all targets.

    Returns:
        DataFrame sorted by target + MAPE :
            model | target | MAPE | RMSE | MAE | n_train | n_test
    """
    results = []
    for target in targets:
        logger.info("Évaluation modèles pour cible '{}'", target)
        results.append(evaluate_prophet(df_monthly, target, n_test))
        results.append(evaluate_xgboost(df_monthly, target, n_test))
        if TF_AVAILABLE:
            results.append(evaluate_lstm(df_monthly, target, n_test=n_test))

    df = (
        pd.DataFrame(results)
        .sort_values(["target", "MAPE"])
        .reset_index(drop=True)
    )
    return df


def log_to_mlflow(
    metrics_df: pd.DataFrame,
    experiment_name: str = "lubricants_forecasting",
) -> None:
    """Log one MLflow run per model × target combination.

    Falls back gracefully if MLflow is not configured.
    """
    if not _MLFLOW_AVAILABLE:
        logger.info("MLflow non disponible — métriques non loggées")
        return

    mlflow.set_experiment(experiment_name)
    for _, row in metrics_df.iterrows():
        with mlflow.start_run(run_name=f"{row['model']}_{row['target']}"):
            mlflow.log_params({
                "model":   row["model"],
                "target":  row["target"],
                "n_train": row.get("n_train", 0),
                "n_test":  row.get("n_test", 0),
            })
            if row["MAPE"] is not None:
                mlflow.log_metrics({
                    "MAPE": row["MAPE"],
                    "RMSE": row["RMSE"],
                    "MAE":  row["MAE"],
                })
    logger.success("Métriques loggées → MLflow (experiment: {})", experiment_name)


def select_best_model(
    metrics_df: pd.DataFrame,
    target: str,
    primary_metric: str = "MAPE",
) -> str:
    """Return the model name with the lowest primary_metric for a given target.

    Falls back to 'prophet' if no valid metrics found.
    """
    sub = metrics_df[
        (metrics_df["target"] == target) & metrics_df[primary_metric].notna()
    ]
    if sub.empty:
        return "prophet"
    best = str(sub.loc[sub[primary_metric].idxmin(), "model"])
    logger.info(
        "Meilleur modèle pour '{}' : {} ({}={:.2f})",
        target, best, primary_metric, sub[primary_metric].min()
    )
    return best
