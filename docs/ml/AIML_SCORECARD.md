# AIML scorecard

Generated from validation-output\ml\baseline.json.
Source: synthetic-workbook; code: 9db3ba47058abf37c86c6c40195db3f70bf5525f; run: 2026-10-23T07:18:10.564964+00:00.

No independent test accuracy is verified by a validation-only run.

| Pillar | Dataset | Test metric | Status |
|---|---|---|---|
| Forecasting | synthetic-workbook | Not evaluated | UNVERIFIED |
| Intent routing | Not evaluated | Not evaluated | UNVERIFIED |
| RAG retrieval | Not evaluated | Not evaluated | UNVERIFIED |
| Anomaly detection | Not evaluated | Not evaluated | UNVERIFIED |
| Product similarity | Not evaluated | Not evaluated | UNVERIFIED |
| Forecast-driven decisions | Not evaluated | Not evaluated | UNVERIFIED |

## Baseline parity diagnostics (not test accuracy)

| Series | Model | One-step MAE | WAPE |
|---|---|---:|---:|
| chain | weekday_mean_28 | 17.339286 | 0.07423547400611621 |
| chain | seasonal_naive_7 | 24.785714 | 0.10611620795107034 |
| chain | naive | 50.571429 | 0.21651376146788992 |
| chain | moving_average_7 | 52.632653 | 0.2253385757972914 |
| chain | exponential_0.3 | 58.754514 | 0.2515483766868294 |

Forecast baselines reproduce the existing algorithm; this does not certify new ML performance. No automatic model promotion.
