# Quantile and feature-importance supplement

This is exploratory pre-test validation, not a reopening or replacement of the final test. SQL reads only dates through April 28, 2026. Freeze one chain-level origin March 31, h=14, embargo April 1-14, score April 15-28. Fit existing histogram quantile adapters at .1/.5/.9 with their fixed parameters. Report raw pinball losses, count crossings, then predeclared per-date sorting and repaired losses/80% coverage/width. No tuning or claims of multi-step calibrated quantiles.

Compare existing weekday-mean-28 baseline with an 80% conformal band: separate February 28 fit predicts March 1-31 to supply residuals; refit point baseline through March 31. Calibration residual dates all precede scored dates, but pooled leads and temporal dependence weaken guarantees. Report both methods, even if poor.

Fit the existing Poisson histogram model through March 31. Generate recursive future features without reading future labels. On the fourteen scored rows, measure seeded five-repeat permutation increase in MAE for every existing feature. This is conditional on fixed recursive history, not a full trajectory perturbation, causal effect or feature selection. No model weights or records leave the machine. Source models and frozen final-test outputs remain unchanged.

Scope adds app/ml/supplement.py, scripts/forecast_supplement.py, tests/ml/test_supplement.py and docs/ml evidence. Run `python -m scripts.forecast_supplement`; it refuses to overwrite evidence. Independent acceptance remains pending, including other origins/levels, pooled models, real benchmark and historical forecast-vintage covariates.
