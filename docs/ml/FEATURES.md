# Feature specification and leakage contract

M14 design only; implementation belongs to M15. See [METHODOLOGY.md](METHODOLOGY.md) for frozen windows and embargo semantics. Prediction cutoff c is the newest allowed information timestamp, not necessarily the day before the scored target. Every derived value must carry source, synthetic flag, observation/effective timestamp and availability timestamp where applicable.

## Proposed modelling table

Key: source snapshot, aggregation level, store/category/SKU as applicable, cutoff, target date and lead. Label: observed units on target date, retained only for training/scoring when observed. Keep coverage mask, training window and exclusion reason alongside the target. Do not put labels or post-cutoff statistics into the model input matrix. Currency preparation uses integer paise or Decimal; numerical model arrays are a separately documented representation.

| Feature | Source | Allowed calculation / availability rule |
|---|---|---|
| Day of week, month, weekend | Target date | Known at cutoff; encode without learning from test data |
| Festival flag | Versioned, verified calendar | Known future date only; no inferred sales-based festival labels |
| Lag 1/7/14/28 | Daily observed quantity | Exact calendar lookup available by cutoff; absent date stays missing, never previous available row |
| Rolling mean/std 7/14/28 | Daily observed quantity | Shift before aggregation; window ends at cutoff or earlier; store valid-day count and do not silently zero-fill |
| Historical price and discount | Transaction payload | Past-only aggregates; future actual transaction values forbidden. Future scheduled prices only if an as-of schedule later exists |
| Channel mix | Historical channel quantities | Past-window proportions; target-day realized mix forbidden; zero denominators stay undefined |
| Competitor price index | Source transaction / weekly estimate | Past-only, using documented availability. Disable weekly features lacking publication evidence rather than using the completed current week |
| Product/store attributes | Catalog and store metadata | Categorical encoders fit on training set; unknown categories have explicit handling; static-as-of assumption documented |
| Weather observations | Future weather table | Observation AND availability timestamps must precede cutoff |
| Weather forecast for target | Archived forecast vintage | Issue time must precede cutoff. Current forecasts and ERA5 future observations cannot stand in for historical forecast vintages |
| Online 15-min / 1-hour totals | Future separate sales_events | Events received by cutoff only; preserve both event time and arrival time; duplicates ignored |
| Previous-week intraday comparator | Future sales_events | Same timezone/hour and equivalent coverage; absent feed coverage is unknown |

Lags at a future target that fall after c are unavailable. Use a declared direct lead model, or recursive predictions with each recursive value marked as predicted; never substitute true later labels. With an h-day embargo, all features and forecasts must honour c, including cutoff-relative rolling windows. Real-time ingestion may receive late events; a historical replay must not use a record before its arrival timestamp.

## Weather experiments

Historical reanalysis is appropriate for lagged observed weather only when availability can be established conservatively. Without archived forecast vintages, future observed weather may appear only in a separate explicitly labelled oracle/sensitivity experiment, never in deployable model selection or headline accuracy. Compare the same eligible folds/models with and without legitimate weather features. Record negative or inconclusive effects; do not promise a gain.

## Preprocessing and labels

All fitted transforms, imputation values and feature selection are trained within each fold. Dropping targets requires a recorded coverage reason; imputation applies only to permitted predictors and uses training-only statistics with missingness indicators. No random train/test shuffle for time series. Global models may pool authorized historical observations but cannot create missing target labels. Train, validation and test source labels must remain visible in results.

For delivery classification, label resolved order lateness only after outcome is known. actual_delivery_date, delay_days_vs_promise and final delivery status are outcomes, not predictors; exclude unknown/unresolved outcomes. If delivery_partner or promised date is only known in a later snapshot, do not assume it was available at order creation. Price-elasticity analysis must describe confounders and correlations; it does not authorize causal price recommendations.

## Required M15/M16 checks

1. Perturb or append all post-cutoff rows: earlier feature vectors and predictions must be identical.
2. Remove an observed day: resulting target/lag stays missing; calendar alignment must not shift.
3. Add extreme validation/test values: fitted encoders, scaling and imputation state must not change.
4. For every generated feature, assert its latest contributing availability timestamp is at or before c.
5. Reproduce baseline numerical outputs on identical eligible rows before adding ML models.
6. Verify currency aggregation equals integer-paise SQL totals; training array conversion must not rewrite ledger values.
7. Test time boundaries, late events, duplicate events, stale weather and unknown categories offline.
8. Verify unauthorized stores and employee fields do not appear in feature exports, predictions or explanations.

These are acceptance requirements, not tests implemented or passed in M14.
