# Apparel conversational forecasting

Branch: agent/demand-forecasting-conversation. This suffix preserves the previously published agent/demand-forecasting source head; no old branch is rewritten.
Owned: app/conversation/forecast.py and test_forecast.py.
Interfaces: ForecastProfile protocol, ApparelRetailForecastProfile, forecast, backtest.
Models: naive, moving average, exponential smoothing; weekly seasonal naive and weekday profile when training history supports them; yearly seasonal naive only with two years of training history.
Evaluation: identical chronological rolling one-step folds per model; no observation after origin; MAE/RMSE selection; WAPE null for zero denominators. Forecast residual bands are explicitly uncalibrated.
Tests: future perturbation does not change results, strict train-before-target, common folds, model choice and zero-sales metrics.
Checklist: [x] model interface [x] baseline competition [x] leakage tests [ ] conversation/UI verification.
Limitations: observed-sales proxy; no fitted promotion/price causality; changing product coverage and date gaps require clarification. Calendar context is configured, not invented.
Knowledge delta: Catalog -> forecast profile -> chronological candidates -> selection -> forecast + evidence + calendar.
