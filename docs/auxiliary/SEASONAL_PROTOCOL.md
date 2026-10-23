# Supplemental seasonal anomaly protocol

Freeze before measuring this supplement. Training: observed daily chain totals through 2026-03-31. Validation: 2026-04-01 through 2026-05-26 (56 days). The SQL query cannot read the already-opened final-test period. No original result is replaced. This is development validation, not independent final-test acceptance.

STL(period=7, seasonal=7, robust=True) fits only training history. Repeat its final weekly component with a flat final trend. Compare absolute residual scores against univariate Isolation Forest (100 trees, contamination .05, seed 42) and absolute deviation from the training median. Each threshold is its training-score 95th percentile; no tuning. Inject five seeded mixed-sign changes of four training standard deviations, clipping at zero, into a copy of validation values. Original arrays are preserved. Report AUROC, average precision, F1, confusion and clean alert rate. Clean alerts cannot be called false positives without natural anomaly labels. In-sample threshold fitting can be optimistic.

Uses already-installed statsmodels 0.14.6; pins match the forecasting environment. Reference: https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.STL.html (currently documents 0.15.0; local tests exercise installed 0.14.6). No model is promoted and no runtime API is changed.

New scope: app/auxiliary/seasonal.py, scripts/evaluate_seasonal_anomalies.py, tests/auxiliary/test_seasonal.py and auxiliary evidence/dependency records. No source-branch merge.
