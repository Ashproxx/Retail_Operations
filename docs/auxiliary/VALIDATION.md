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
