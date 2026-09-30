# Apparel conversational forecasting

Branch: agent/demand-forecasting-conversation. This suffix preserves the previously published agent/demand-forecasting source head; no old branch is rewritten.
Owned: app/conversation/forecast.py and test_forecast.py.
Interfaces: ForecastProfile protocol, ApparelRetailForecastProfile, forecast, backtest.
Models: naive, moving average, exponential smoothing; weekly seasonal naive and weekday profile when training history supports them; yearly seasonal naive only with two years of training history.
Evaluation: identical chronological rolling one-step folds per model; no observation after origin; MAE/RMSE selection; WAPE null for zero denominators. Forecast residual bands are explicitly uncalibrated.
Tests: future perturbation does not change results, strict train-before-target, common folds, model choice and zero-sales metrics.
Checklist: [x] model interface [x] baseline competition [x] leakage tests [x] conversation/UI verification.
Limitations: observed-sales proxy; no fitted promotion/price causality; changing product coverage and date gaps require clarification. Calendar context is configured, not invented.
Knowledge delta: Catalog -> forecast profile -> chronological candidates -> selection -> forecast + evidence + calendar.

Integrated verification (2026-09-30): local Python suite and both real-browser gates passed. See `docs/conversation/VALIDATION.md` for tested scope and commit evidence. Feature checkpoints remain unchanged; this annotation belongs to the integration candidate.

Remote feature/checkpoint SHA: `c4b0d7e77f7eb10c42f35fe7c4cad40c4e2b156f`. Integration verification target: `c613603e503f675d9da2651d05e3af07438f54f1`; final CI evidence is recorded in `docs/conversation/VALIDATION.md`.
