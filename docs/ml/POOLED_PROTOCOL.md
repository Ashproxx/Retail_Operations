# Pooled boosting development protocol

Fixed before measurement: one shared Poisson histogram boosting model per hierarchy level (store and store/category), compared to independent local histogram models and the existing weekday-mean baseline. All use the same 56 observed training dates ending March 31, 2026. Score April 15-28 after a fourteen-day embargo. SQL reads only February 4-April 28. Require every training/scoring date to exist, without inventing zero sales. Report excluded series; fewer than two eligible series means pooling is unverified.

Reuse the existing eleven past-only lag/calendar features. Add one-hot series identity to the pooled model. Each series contributes exactly 28 supervised rows after lag construction, with equal row weight. Freeze 100 iterations, 15 leaves, minimum leaf 10, Poisson loss, seed 42 and no early stopping, matching the local adapter. Recursive features use predictions from the preceding days, including the embargo; scoring labels never enter fitting or prediction.

Report per-series point metrics for all three fixed methods. No selection, significance, intervals or promotion is claimed. This is exploratory development evidence after the primary test was opened, not a fresh independent test. Sparse store/category coverage may prevent that level's evaluation. New/unseen series are rejected. Runtime scope and baseline fallback remain unchanged because this module is not mounted in the website.

Run `python -m scripts.evaluate_pooled_forecasting` after committing the implementation. Evidence refuses overwrite, pins the exact code commit and hashes the aggregate source. No primary artifacts are rerun or rewritten.
