# Module 4 — Forecasting

## Objectif
Prédire le volume vendu, le prix base oil (proxy WTI) et la marge brute
à 30, 60 et 90 jours pour alimenter les inputs IBP.

## Statut
Non démarré

## Fichiers à créer
- [ ] `prophet_model.py` — forecast saisonnalité (pic nov-fév lubrifiant)
- [ ] `xgboost_model.py` — forecast avec drivers macro (Brent, inflation, XOF)
- [ ] `lstm_model.py` — patterns long terme (TensorFlow/Keras)
- [ ] `model_comparison.py` — comparaison MAPE/RMSE/MAE + MLflow
- [ ] `forecast_pipeline.py` — pipeline complète avec walk-forward validation

## Modèles et rôles
| Modèle | Rôle | Variables exogènes |
|--------|------|--------------------|
| Prophet | Saisonnalité mensuelle | Jours fériés, seasonality_mode=multiplicative |
| XGBoost | Drivers macro | prix_brent_usd, taux_usd_local, inflation_locale, lags t-1/t-3/t-6 |
| LSTM | Patterns séquentiels | Séquences 12 mois glissants |

## Validation
- Walk-forward validation : entraînement sur n mois, test sur 6 mois suivants
- Horizon forecast : 30j / 60j / 90j
- Métriques : MAPE, RMSE, MAE sur out-of-fold

## KPIs cibles
- MAPE prix base oil 30j < 5%
- MAPE volume SKU 30j < 8%
- RMSE marge mensuelle < 120 FCFA/L

## Inputs
- `data/processed/transactions_features.parquet` (features engineered)
- EIA API : prix WTI historique
- World Bank API : inflation historique
- Frankfurter API : taux USD/XOF historique

## Outputs
- `data/processed/forecasts_30_60_90.parquet`
- MLflow experiments : `mlruns/`
