# AIML scorecard

Source: synthetic-workbook. Measured final-test implementation: c1e872fd5f331f42010b56a7c3019dd1d597c278. Date: 2026-10-23.

| Pillar | Evidence / metric | Status |
|---|---|---|
| Forecasting | Frozen chain/store comparison, MAE/RMSE/WAPE/MASE/bias and empirical interval coverage in MODEL_COMPARISON.md | VERIFIED for the explicitly scored subset only |
| Routing | 200 draft-labelled cases; accuracy 0.51, macro-F1 0.5871, 116 abstentions; human review blank | DRAFT DIAGNOSTIC ONLY |
| RAG | 50 authored positives / 15 negatives; Recall@1 0.98, but only 17/50 positive answers returned evidence | FICTIONAL DEVELOPMENT FIXTURE ONLY |
| Anomaly detection | STL, Isolation Forest and median baseline detect five injected anomalies; no superiority demonstrated | INJECTION PROXY ONLY |
| Similarity/segmentation | Top-five geometric overlap 0.743529; Spearman 0.795624; 534 directed pairs await human review | METHOD AGREEMENT ONLY |
| Forecast-driven decisions | Price association with uncertainty measured; no measured stockout benefit or causal pricing evidence | DESCRIPTIVE ONLY |

Chain h=28: selected-before-test weekday_mean_28 baseline, test WAPE 13.5636%, MAE 30.8839 units across 56 observations. This uses the required embargo and two test blocks, not ordinary next-day operational accuracy. Its empirical 80% band covered 67.86% and 95% band covered 85.71%; nominal coverage was not achieved. Do not hide this calibration weakness. Histogram boosting was worse on this comparison (WAPE 14.8524%).

180 validation model records were attempted across 12 eligible series (chain plus 11 stores); 716 model/horizon test attempts include 60 missing-coverage/fit failures. 9 stores, all 120 store/category series and all 1,700 store/SKU series were excluded under the predeclared complete-window requirement. Four candidates are eligible for review under exploratory gates; none is promoted. Four series/horizon choices lack paired final-test coverage. No real-world accuracy claim.

M17 is not fully accepted. Pooled boosting, quantiles and feature importance now have bounded development supplements below; time-safe weather/festival ablation, broader independent comparisons, a real benchmark and independent review remain outstanding. See FORECAST_RESULTS.json for the original frozen comparison's exact failures, decisions and limitations. Its historical limitations describe that run, not subsequent supplements.


## Pre-test quantile / importance supplement

At frozen code 4e17558, one chain h=14 origin (March 31, scoring April 15-28) measured .1/.5/.9 quantile pinball losses of 4.8149 / 9.7629 / 8.6392. No crossing occurred. Both quantile and baseline conformal 80% bands covered all 14 observations; mean widths were 134.54 and 139 units respectively. This tiny development validation window does not establish calibration or improvement; primary final-test undercoverage remains unchanged.

All eleven existing Poisson-boosting features have measured permutation MAE changes in QUANTILE_IMPORTANCE_RESULTS.json. They describe fixed recursive feature rows and correlated predictive associations, not causal importance or full rollout perturbations. Models never saw validation target labels during fitting or recursive feature generation. Existing final-test artifacts were neither reopened nor changed. Broader independent comparisons, real benchmark and weather/festival-vintage evidence remain pending.

## Reconciled supplement evidence — 2026-10-29

[POOLED_RESULTS.json](POOLED_RESULTS.json) compares thirteen eligible stores on April 15–28 development data: mean store WAPE 40.1802% pooled, 46.0297% local boosting and 40.2994% weekday baseline. Only six stores favor pooling. Seven stores and all 120 store/category series were excluded for missing observations. No superiority, promotion or independent final-test claim follows from this small mean difference.

[Auxiliary validation](../auxiliary/VALIDATION.md) records the frozen router, retrieval, seasonal anomaly, price and similarity supplements with their protocols. The descriptive log-price coefficient is -0.2484 with week-cluster interval [-0.3862, -0.1106]; confounding and price/quantity coupling prevent causal interpretation. Delivery candidates still lose to the prevalence baseline on Brier score. Human labels, natural anomalies, actual policies and genuine inventory/lead-time outcomes remain evidence gaps.

This reconciliation changes no model, frozen metric, label or selection. The integrated engineering checks are in [integration validation](../ml-integration/VALIDATION.md); the separate simulated live dataset has its own [acceptance map](../live-demo/COVERAGE.md). Simulation does not satisfy the real-data gates.
