# Forecasting technique survey

Scope: measured synthetic-workbook candidates, not a claim that a complex model wins. Reviewed 2026-10-23. Optional implementation dependencies are isolated in requirements-ml.txt; default website startup does not need them.

| Technique | Idea / assumptions | Strength | Limitation / decision |
|---|---|---|---|
| Existing five baselines | Last observation, recent mean, fixed exponential level or weekly pattern | Cheap, transparent and retained fallback | Weak fitted covariates; always benchmark |
| ETS | Additive level/trend and weekly seasonality; damped trend | Small data, interpretable seasonality | Requires regular observations; kept |
| SARIMA | Fixed AR(1) plus seasonal AR(1) at lag 7 | Weekly serial structure | Optimizer can fail; failures reported rather than hidden |
| Calendar SARIMAX | SARIMA with target-known weekly/monthly sine/cosine terms | Explicit known exogenous calendar | Weather/festival version remains unverified without time-safe inputs |
| Croston/SBA/TSB | Separate positive-event size and spacing/probability | Meaningful for genuine intermittent counts | Unknown dates are not zero; positive-only workbook does not validate stockout/intermittency claims |
| Gamma–Poisson | Gamma(1,1) prior updated by count sum and observed-day exposure | Explicit simple posterior mean | No seasonality, independent-rate assumption; retained as a transparent sparse-count comparison |
| Ridge/Lasso | Penalized regression on calendar, lags and rolling history | Interpretable, train-only scaling | Recursive errors accumulate; kept |
| Histogram gradient boosting | Nonlinear lag/calendar model with Poisson loss | Handles nonlinearities without an extra boosting library | Local per-series adapter; global pooled training remains incomplete |
| Random Forest/ExtraTrees | Averaged randomized trees | Robust nonlinear comparison | Adapters unit-tested but not part of the frozen primary leaderboard |
| Quantile boosting | Separate conditional quantile fits | Direct uncertainty comparison | Adapter tested; full pinball/coverage comparison remains outstanding |
| Split conformal | Finite-sample absolute-error quantile on separate calibration residuals | Model-independent bands with measurable coverage | Temporal dependence and pooled leads weaken exchangeability; empirical coverage must be shown |
| Prophet / neural / pretrained models | Optional additional model families | Potential alternate seasonality/global knowledge | Deferred: no evidence yet justifies install or weights; one year is limited |
| Ensembles / hierarchy reconciliation | Combine predictions and reconcile sums | Potential stability and consistent totals | Deferred; missing lower-level observations prevent a defensible complete hierarchy |

The implementation uses one predefined setting per model, below the 30-trial budget. This is a reproducible comparison, not an exhaustive tuning claim. Data eligibility is decided before model comparison. Zero-fill and observed future weather would make the experiment misleading and are not used.

## Sources actually opened

- [statsmodels ExponentialSmoothing API](https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.ExponentialSmoothing.html): seasonal/trend options and fit interface.
- [statsmodels SARIMAX API](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html): statistical/exogenous model interface.
- [scikit-learn linear models](https://scikit-learn.org/stable/modules/linear_model.html): penalized linear regression assumptions.
- [HistGradientBoostingRegressor API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html): Poisson/quantile losses, iteration and early-stopping controls.
- [Forecasting: Principles and Practice, practical issues](https://otexts.com/fpp3/practical.html): intermittent counts, missing observations, practical forecasting limits.
- [Angelopoulos and Bates, conformal prediction tutorial](https://arxiv.org/abs/2107.07511): split-conformal framework and caveats for structured data.

Documentation on the stable statsmodels site currently describes a newer version than the pinned local 0.14.6 implementation; local adapter tests verify the interfaces actually used. No source is cited as proving performance on this project's dataset.
