# M17 checkpoint — 2026-10-23

Branch based on ca22a9f as authorized; no integration/main changes.

Implemented and unit-tested: four sparse-count adapters, conformal finite-sample bands, pinball loss and empirical interval metrics. They are framework candidates, not demonstrated improvements on retail data. Intermittent methods require genuine observed zero labels; workbook gaps remain unknown. Gamma–Poisson uses a documented Gamma(1,1) prior and exposes posterior shape/rate; it makes no seasonal claim.

Next: implement statistical and tabular models, freeze candidate configurations and fit only pre-test data, generate validation evidence and calibrate on separate residuals before opening the untouched test block. Benchmark availability/coverage at each hierarchy level, report exclusions, verify weather-vintage availability, and compare with the simplest eligible baseline. M18 auxiliary evaluation and M19 dashboard remain on separate branches. M20 integration is not authorized.

Checks: `python -m pytest tests/ml -q` -> 7 passed. No full regression rerun for this isolated checkpoint. No model promotion or final-test access.
