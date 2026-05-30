"""LSTM forecasting model — M4 Forecasting.

Pourquoi LSTM ?
    Les contrats annuels en B2B créent des dépendances à mémoire longue :
    une décision de prix en janvier influence les commandes jusqu'en juin.
    LSTM (Long Short-Term Memory) est conçu pour ces dépendances que
    Prophet et XGBoost ne capturent pas.

Note sur les données synthétiques :
    Sur 36 mois, le LSTM est en mode "preuve de concept". Il bénéficiera
    pleinement de 3+ ans de données réelles supplémentaires.
"""

import numpy as np
import pandas as pd
from loguru import logger

try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow non disponible — LSTM désactivé (installer tensorflow==2.18.0)")

SEQ_LEN = 6  # 6 mois de lookback (adapté aux 36 points disponibles)


def _prepare_sequences(series_norm: np.ndarray, seq_len: int) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for i in range(len(series_norm) - seq_len):
        X.append(series_norm[i:i + seq_len])
        y.append(series_norm[i + seq_len])
    return np.array(X), np.array(y)


def build_lstm(seq_len: int = SEQ_LEN) -> "keras.Sequential":
    """Build a simple LSTM architecture (1 layer — adapté à un petit dataset).

    Returns:
        Compiled Keras model.
    """
    model = keras.Sequential([
        keras.layers.LSTM(32, input_shape=(seq_len, 1), return_sequences=False),
        keras.layers.Dropout(0.1),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def train_lstm(
    df_monthly: pd.DataFrame,
    target: str,
    seq_len: int = SEQ_LEN,
    epochs: int = 150,
) -> tuple["keras.Sequential", float, float]:
    """Train LSTM on normalized target series.

    Returns:
        Tuple (model, mean_scaler, std_scaler) for denormalization.
    """
    if not TF_AVAILABLE:
        raise RuntimeError("TensorFlow non disponible.")

    series     = df_monthly[target].values.astype(float)
    mean_val   = float(series.mean())
    std_val    = float(series.std()) if series.std() > 0 else 1.0
    series_norm = (series - mean_val) / std_val

    X, y = _prepare_sequences(series_norm, seq_len)
    X    = X.reshape(X.shape[0], X.shape[1], 1)

    model = build_lstm(seq_len)
    model.fit(
        X, y,
        epochs=epochs,
        batch_size=8,
        validation_split=0.1,
        verbose=0,
        callbacks=[
            keras.callbacks.EarlyStopping(patience=20, restore_best_weights=True)
        ],
    )
    logger.info(
        "LSTM entraîné : {} séquences | cible '{}' | seq_len={}",
        len(X), target, seq_len
    )
    return model, mean_val, std_val


def predict_lstm(
    model: "keras.Sequential",
    df_monthly: pd.DataFrame,
    target: str,
    mean_val: float,
    std_val: float,
    seq_len: int = SEQ_LEN,
    horizon_months: int = 3,
) -> pd.DataFrame:
    """Recursive multi-step LSTM forecast.

    Returns:
        DataFrame with columns: ds | yhat | model
    """
    if not TF_AVAILABLE:
        raise RuntimeError("TensorFlow non disponible.")

    series      = df_monthly[target].values.astype(float)
    series_norm = (series - mean_val) / std_val
    history     = list(series_norm[-seq_len:])
    last_date   = pd.to_datetime(df_monthly["date"].iloc[-1])
    forecasts   = []

    for step in range(horizon_months):
        X_input = np.array(history[-seq_len:]).reshape(1, seq_len, 1)
        y_norm  = float(model.predict(X_input, verbose=0)[0][0])
        y_hat   = y_norm * std_val + mean_val
        next_date = last_date + pd.DateOffset(months=step + 1)
        forecasts.append({"ds": next_date, "yhat": round(y_hat, 2), "model": "lstm"})
        history.append(y_norm)

    return pd.DataFrame(forecasts)


def evaluate_lstm(
    df_monthly: pd.DataFrame,
    target: str,
    seq_len: int = SEQ_LEN,
    n_test: int = 6,
) -> dict[str, object]:
    """Walk-forward evaluation.

    Returns:
        Dict with model, target, MAPE, RMSE, MAE (None if TF unavailable).
    """
    if not TF_AVAILABLE:
        logger.warning("LSTM désactivé — résultats null")
        return {
            "model": "lstm", "target": target,
            "MAPE": None, "RMSE": None, "MAE": None,
            "n_train": 0, "n_test": n_test,
        }

    train_df = df_monthly.iloc[:-n_test].copy()
    test_df  = df_monthly.iloc[-n_test:].copy()

    model, mean_val, std_val = train_lstm(train_df, target, seq_len)
    forecast = predict_lstm(model, train_df, target, mean_val, std_val, seq_len, horizon_months=n_test)

    y_true = test_df[target].values
    y_pred = forecast["yhat"].values[:len(y_true)]
    denom  = np.where(np.abs(y_true) < 1e-6, 1.0, y_true)

    mape = float(np.mean(np.abs((y_true - y_pred) / denom)) * 100)
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae  = float(np.mean(np.abs(y_true - y_pred)))

    logger.info(
        "LSTM eval [{}] — MAPE: {:.2f}% | RMSE: {:.2f} | MAE: {:.2f}",
        target, mape, rmse, mae
    )
    return {
        "model": "lstm", "target": target,
        "MAPE": round(mape, 4), "RMSE": round(rmse, 2), "MAE": round(mae, 2),
        "n_train": len(train_df), "n_test": n_test,
    }
