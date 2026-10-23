# AIML scorecard

Source: synthetic-workbook. Measured final-test implementation: c1e872fd5f331f42010b56a7c3019dd1d597c278. Date: 2026-10-23.

| Pillar | Evidence / metric | Status |
|---|---|---|
| Forecasting | Frozen chain/store comparison, MAE/RMSE/WAPE/MASE/bias and empirical interval coverage in MODEL_COMPARISON.md | VERIFIED for the explicitly scored subset only |
| Routing | Human-reviewed benchmark not yet complete | UNVERIFIED |
| RAG | Expanded benchmark not yet evaluated | UNVERIFIED |
| Anomaly detection | No new measured benchmark yet | UNVERIFIED |
| Similarity/segmentation | No new measured benchmark yet | UNVERIFIED |
| Forecast-driven decisions | No measured stockout or causal pricing evidence | UNVERIFIED |

Chain h=28: selected-before-test weekday_mean_28 baseline, test WAPE 13.5636%, MAE 30.8839 units across 56 observations. This uses the required embargo and two test blocks, not ordinary next-day operational accuracy. Its empirical 80% band covered 67.86% and 95% band covered 85.71%; nominal coverage was not achieved. Do not hide this calibration weakness. Histogram boosting was worse on this comparison (WAPE 14.8524%).

180 validation model records were attempted across 12 eligible series (chain plus 11 stores); 716 model/horizon test attempts include 60 missing-coverage/fit failures. 9 stores, all 120 store/category series and all 1,700 store/SKU series were excluded under the predeclared complete-window requirement. Four candidates are eligible for review under exploratory gates; none is promoted. Four series/horizon choices lack paired final-test coverage. No real-world accuracy claim.

M17 is not fully accepted: time-safe weather/festival ablation, global pooled boosting, quantile comparison, full feature-importance coverage, real benchmark and independent review remain outstanding. See FORECAST_RESULTS.json for exact failures, per-series decisions and limitations.
