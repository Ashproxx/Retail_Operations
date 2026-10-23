# M17 checkpoint â€” 2026-10-23

Branch based on ca22a9f as authorized; no integration/main changes.

Implemented and unit-tested: four sparse-count adapters, conformal finite-sample bands, pinball loss and empirical interval metrics. They are framework candidates, not demonstrated improvements on retail data. Intermittent methods require genuine observed zero labels; workbook gaps remain unknown. Gammaâ€“Poisson uses a documented Gamma(1,1) prior and exposes posterior shape/rate; it makes no seasonal claim.

Next: implement statistical and tabular models, freeze candidate configurations and fit only pre-test data, generate validation evidence and calibrate on separate residuals before opening the untouched test block. Benchmark availability/coverage at each hierarchy level, report exclusions, verify weather-vintage availability, and compare with the simplest eligible baseline. M18 auxiliary evaluation and M19 dashboard remain on separate branches. M20 integration is not authorized.

Checks: `python -m pytest tests/ml -q` -> 7 passed. No full regression rerun for this isolated checkpoint. No model promotion or final-test access.


Second checkpoint: optional statsmodels ETS/SARIMA/calendar-SARIMAX and scikit-learn Ridge/Lasso/Poisson histogram boosting adapters are implemented, along with tested forest and quantile adapters. Dependencies are isolated in requirements-ml.txt; statsmodels is justified because the existing code has no statistical optimizer. The other libraries were already installed; versions are now pinned for reproduction. All 18 ML tests pass. A frozen two-stage benchmark will compare 15 primary candidates at all four levels where contiguous coverage permits. Unsupported series are explicitly excluded, not zero-filled. Calendar SARIMAX is not presented as weather/festival SARIMAX: historical forecast vintages and verified festival availability remain missing. Test block is still unopened at this checkpoint.
