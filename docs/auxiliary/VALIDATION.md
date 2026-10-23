# Auxiliary evaluation results

M18 PARTIAL. Source: synthetic workbook. Frozen implementation: 6dbcf827be36c3484b5cdb5d5a50013c8ceadd1e. Seed 42. No model is deployed.

## Delivery risk

Training: 17,174 resolved delivered orders. Excluded: {'unresolved_or_missing_actual': 2807, 'label_unavailable_at_partition_end': 602}. Each order is counted once; labels must be available at the partition boundary.

| Model | Test orders | ROC-AUC | Average precision | Brier (lower better) | ECE |
|---|---:|---:|---:|---:|---:|
| prevalence_baseline | 4826 | 0.5000 | 0.4760 | 0.2536 | 0.0649 |
| logistic | 4826 | 0.5645 | 0.5366 | 0.2597 | 0.1172 |
| forest | 4826 | 0.5573 | 0.5310 | 0.2557 | 0.0955 |

Neither candidate beats the prevalence baseline on Brier score. Discrimination is weak. Retain existing descriptive delivery reporting; do not serve these probabilities as reliable operational risk.

## Product clusters

85 products; fixed three clusters of sizes 47, 37 and 1. In-sample silhouette 0.3974. The singleton and exposure differences limit usefulness. This does not establish similarity ranking accuracy.

## Injected anomalies

Isolation Forest and the simple median-absolute-deviation baseline both detected all five large injected upward spikes in 56 held-out days (F1 1.0). This intentionally easy, synthetic proxy establishes no superiority and no accuracy on natural anomalies. Clean holdout alert rate was zero; natural anomaly labels are unavailable, so this is not a measured false-positive rate.

## Remaining gates

Human-reviewed router queries, expanded signed-RAG evaluation, seasonal STL comparison, similarity ranking agreement, price-effect uncertainty and real stockout labels remain unverified. No automated employment, inventory or pricing action is introduced. No data is sent to external services.

Run: `python -m scripts.evaluate_auxiliary` with the existing imported local database and requirements-auxiliary.txt. The command refuses to overwrite existing results. Preserve this frozen output; future tuning needs new evaluation data. Raw inputs remain local.

Validation: 7 focused tests; full regression result recorded in branch deliverables. Only owned auxiliary paths and branch records changed; inherited source implementations are untouched.

Measured checks: 7 auxiliary tests passed; full regression 221 passed in 23.20 seconds.


## Seasonal anomaly supplement

SEASONAL_RESULTS.json records fixed implementation e384d6c on April 1-May 26 development validation, with training ending March 31. STL weekly residuals, Isolation Forest and median deviation each detected all five large mixed-sign injections (AUROC/AP/F1 1.0; confusion 51/0/0/5; clean alert rate 0). This easy proxy shows no superiority of STL over simpler methods. It is not natural anomaly accuracy, independent final-test evidence or a false-positive-rate estimate. The original RESULTS.json remains untouched. No tuning, model promotion or production wiring occurred.

Tests verify that changing validation values cannot change any training threshold, source arrays remain unchanged, missing days are rejected, and later dates cannot enter the supplement. Nine focused auxiliary tests pass. See SEASONAL_PROTOCOL.md for reproduction scope and assumptions.

Supplement regression: 223 passed in 29.66 seconds. Existing final-test evidence was not rerun.


## Expanded retrieval development fixture

Frozen implementation 72282a4 measured 50 authored positives and 15 negatives over ten fictional policy documents using a local TF-IDF baseline and the unchanged signed RAG pipeline. Recall@1 0.98, Recall@3 1.00, MRR@3 0.99, nDCG@3 0.9926. All 15 negatives abstained, but only 17/50 positives returned evidence: abstention precision is 0.3125. Strong raw retrieval does not establish usable answer coverage. No thresholds or labels were changed after observing these results. No scope leaks were observed with the forbidden-store decoy. These labels are NOT human-reviewed and are not actual retail policy.

The first run wrote complete results but exited with a Windows file-lock cleanup error. The evaluator now explicitly closes the Chroma client before temporary-directory cleanup; a focused lifecycle test verifies removal after an indexed document. Frozen metrics were preserved and were not rerun to conceal failures. Automatic approval review rejected a later cleanup command as blocked by policy, so the original temporary artifact was left alone. See RAG_RESULTS.json, RAG_FIXTURE.json and RAG_PROTOCOL.md. No model download, external request or production wiring.

Expanded retrieval checks: 12 auxiliary tests in total; full regression 226 passed in 28.15 seconds. Chroma lifecycle test passed on Windows.
