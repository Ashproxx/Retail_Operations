# M18 auxiliary evaluations - frozen protocol

Branch ml/auxiliary-models, based on showcase c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. No cross-branch merge, runtime hook or protected-branch change.

Scope: app/auxiliary, tests/auxiliary, scripts/evaluate_auxiliary.py, requirements-auxiliary.txt, docs/auxiliary and these branch records. Read-only local CLI; results contain aggregate metrics, no customer/employee records. Dependencies are already installed and pinned separately.

Fixed protocol before first test evaluation: delivery models train on resolved delivered orders sold and resolved by March 31; validation April 1-August 4, test August 5-September 29. Labels must be resolved by each partition end. No tuning or refitting. Logistic C=1 and forest 100 trees/depth 8/min-leaf 20 compare with training prevalence. Threshold .5. Preprocessors fit only training rows; each order counted once; conflicting lines excluded. Record ROC-AUC, average precision, Brier, calibration bins, ECE and confusion matrices. Missing outcome labels are not negatives.

Segmentation: train-period observed product features, fixed k=3 and seed 42; report descriptive in-sample silhouette, not held-out accuracy. Anomalies: train-period daily counts; five seeded upward spikes in a copy of the 56-day test block; fixed IsolationForest versus median-absolute-deviation baseline, thresholds from training 95th percentile. No natural anomaly labels, no false-positive-rate claim. This separate proxy task does not retune M17 forecasting.

Pending/unverified: human-reviewed router labels, expanded signed-RAG benchmark, STL seasonal anomaly comparison, similarity ranking agreement, price-effect uncertainty and stockout labels. No acceptance or real-world performance claim before measurement. M20 requires exact-commit approval.

