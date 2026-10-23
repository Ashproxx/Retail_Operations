# M17 checkpoint â€” 2026-10-23

Branch based on ca22a9f as authorized; no integration/main changes.

Implemented and unit-tested: four sparse-count adapters, conformal finite-sample bands, pinball loss and empirical interval metrics. They are framework candidates, not demonstrated improvements on retail data. Intermittent methods require genuine observed zero labels; workbook gaps remain unknown. Gammaâ€“Poisson uses a documented Gamma(1,1) prior and exposes posterior shape/rate; it makes no seasonal claim.

Next: implement statistical and tabular models, freeze candidate configurations and fit only pre-test data, generate validation evidence and calibrate on separate residuals before opening the untouched test block. Benchmark availability/coverage at each hierarchy level, report exclusions, verify weather-vintage availability, and compare with the simplest eligible baseline. M18 auxiliary evaluation and M19 dashboard remain on separate branches. M20 integration is not authorized.

Checks: `python -m pytest tests/ml -q` -> 7 passed. No full regression rerun for this isolated checkpoint. No model promotion or final-test access.


Second checkpoint: optional statsmodels ETS/SARIMA/calendar-SARIMAX and scikit-learn Ridge/Lasso/Poisson histogram boosting adapters are implemented, along with tested forest and quantile adapters. Dependencies are isolated in requirements-ml.txt; statsmodels is justified because the existing code has no statistical optimizer. The other libraries were already installed; versions are now pinned for reproduction. All 18 ML tests pass. A frozen two-stage benchmark will compare 15 primary candidates at all four levels where contiguous coverage permits. Unsupported series are explicitly excluded, not zero-filled. Calendar SARIMAX is not presented as weather/festival SARIMAX: historical forecast vintages and verified festival availability remain missing. Test block is still unopened at this checkpoint.


Final measured checkpoint (supersedes the earlier test-unopened status): frozen implementation c1e872f evaluated the predeclared August 5 and September 2 blocks once. Reports published at e72d8d9. Full regression: 232 passed; ML suite: 18 passed. Chain h=28 weekday baseline WAPE 13.5636%; histogram boosting 14.8524%. Nominal interval coverage was not achieved. All exclusions and failures remain visible in FORECAST_RESULTS.json. No promotion or integration occurred. M17 remains partial for the gaps listed in AIML_SCORECARD.md; final-test results cannot be used to retune models and claim independent improvement on this same holdout.


## Pre-test quantile / importance supplement

At frozen code 4e17558, one chain h=14 origin (March 31, scoring April 15-28) measured .1/.5/.9 quantile pinball losses of 4.8149 / 9.7629 / 8.6392. No crossing occurred. Both quantile and baseline conformal 80% bands covered all 14 observations; mean widths were 134.54 and 139 units respectively. This tiny development validation window does not establish calibration or improvement; primary final-test undercoverage remains unchanged.

All eleven existing Poisson-boosting features have measured permutation MAE changes in QUANTILE_IMPORTANCE_RESULTS.json. They describe fixed recursive feature rows and correlated predictive associations, not causal importance or full rollout perturbations. Models never saw validation target labels during fitting or recursive feature generation. Existing final-test artifacts were neither reopened nor changed. Global pooling, broader independent comparisons, real benchmark and weather/festival-vintage evidence remain pending.

Supplement point comparison: quantile median WAPE 8.8295% versus weekday baseline 10.1744% on the same fourteen development observations, without a significance or deployment claim. Negative permutation values are retained: they can indicate harmful/redundant features on this small sample, not causal effects. No feature was removed or model retuned.

Supplement verification: 20 focused ML tests including two new checks; full regression 234 passed in 28.77 seconds. Branch-scope/source-preservation guard passed.
