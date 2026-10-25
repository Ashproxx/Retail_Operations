# M18 auxiliary evaluations - measured partial checkpoint

Branch ml/auxiliary-models, based on showcase c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. No cross-branch merge, runtime hook or protected-branch change.

Measured results: docs/auxiliary/VALIDATION.md and RESULTS.json. Delivery candidates have worse Brier scores than the prevalence baseline; no promotion. Clustering is descriptive; anomaly metrics apply only to five large injected spikes. M18 remains partial.

Scope: app/auxiliary, tests/auxiliary, scripts/evaluate_auxiliary.py, scripts/evaluate_seasonal_anomalies.py, requirements-auxiliary.txt, docs/auxiliary and these branch records. Read-only local CLI; results contain aggregate metrics, no customer/employee records. Dependencies are already installed and pinned separately.

Fixed protocol before first test evaluation: delivery models train on resolved delivered orders sold and resolved by March 31; validation April 1-August 4, test August 5-September 29. Labels must be resolved by each partition end. No tuning or refitting. Logistic C=1 and forest 100 trees/depth 8/min-leaf 20 compare with training prevalence. Threshold .5. Preprocessors fit only training rows; each order counted once; conflicting lines excluded. Record ROC-AUC, average precision, Brier, calibration bins, ECE and confusion matrices. Missing outcome labels are not negatives.

Segmentation: train-period observed product features, fixed k=3 and seed 42; report descriptive in-sample silhouette, not held-out accuracy. Anomalies: train-period daily counts; five seeded upward spikes in a copy of the 56-day test block; fixed IsolationForest versus median-absolute-deviation baseline, thresholds from training 95th percentile. No natural anomaly labels, no false-positive-rate claim. This separate proxy task does not retune M17 forecasting.

Pending/unverified: human-reviewed router labels, human-reviewed semantic retrieval acceptance, independent natural-anomaly validation, similarity ranking agreement, price-effect uncertainty and stockout labels. No acceptance or real-world performance claim before measurement. M20 requires exact-commit approval.

---

## Inherited branch record

# integration/dual-model-retailops

Current Phase 3 integration: [branch ownership](docs/branches/integration-dual-model-retailops.md), [validation report](docs/phase3/VALIDATION.md), [runbook](docs/phase3/RUNBOOK.md). Composes imported sales and employees with two active workspaces and two Coming Soon models. Main remains human-controlled. Earlier release records below are retained as historical evidence and do not determine Phase 3 completion.

## Historical integration/release-candidate

Base: foundation/core-platform `77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045`.
Human explicitly approved the exact sources in `docs/integration/APPROVED_SOURCES.json`, including security `e55f640b416d2109bac8fbf9dea2622dbdc78577`. Approval covers this candidate only; no main merge is authorized.

M13: INCOMPLETE. Official weighted completion: 95% (M0-M12 passed). All available local integration work is implemented. Real-data mapping and business-output validation remain unverified because no operational dataset was supplied. Model and container/remote-CI gates have now been executed successfully.

## Scope and interfaces

Preserve source agent/router/RAG/security files byte-for-byte. Integrate through `app/integration`: registry, parameter bridge, LangGraph orchestration, authenticated routes, atomic CSV/XLSX loader, SQL repository, signed retrieval wrapper, local provider protocol, owned memory/feedback and CLI/demo.

SHARED DELTA: API registration in app/main.py, shared dependencies/env settings, tests/foundation route expectations, branch guard, Docker/CI and global integrated docs/graphs. Original metadata is archived by source branch under docs/integration/sources. Source branch refs are not modified.

Dependencies: existing LangGraph/Chroma/sentence-transformers branch requirements are installed centrally; existing httpx test dependency is now used by the local Ollama adapter. openpyxl (>=3.1,<4) is the only additional functional library, required for XLSX reading; CSV uses the standard library. CPU PyTorch is installed first to avoid unnecessary CUDA dependencies. No paid provider required.

SQL stores validated domain payloads keyed by immutable observation identity, plus store names, session state, request receipts/feedback and signed manifests. This is an explicit schema adapter pending actual production column inspection, not a fabricated business database. See README for source-to-field mappings and per-agent schema export.

## Validation and limitations

Run `python -m pytest -q`, `python scripts/check_branch_scope.py`, `python -m app.integration.demo` and `python -m pip check`. Latest results: docs/integration/REPORT.md. Uvicorn startup/health/OpenAPI are verified separately. Token provisioning is tested without printing secrets.

No real retail dataset was supplied. Expanded remote CI run 35909119561 passed Docker build/runtime/restart, actual Ollama inference, and pinned pretrained MiniLM retrieval on a labelled synthetic set. Docker execution took place on the GitHub runner, not this local workspace. Role/store checks precede reads; audit is single-writer with independent anchors required across restarts. Natural-language rules are bounded; unsupported/missing parameters escalate. Numerical confidence is not calibrated. No production transactions or notifications are executed. Full limitations and setup are in README and ARCHITECTURE.md.

Published implementation: `1b50c1ea9e4a116cc5da04ba9df6efb2e46b9f0c`. Fetched tree matches the tested local tree. Full suite: 178 passed, 0 failed, 0 skipped. Graph: 500 nodes / 786 edges. All fourteen pre-existing refs verified unchanged. Final documentation SHA is recorded in the session response.

## Remaining-work validation extension

Previous remote CI including Docker build is verified successful: run 35878697558 at `9e939b2519f314281cf246e224206aefa6eaff8d`. Added explicit pinned pretrained-model evaluation, real Ollama smoke and authenticated container/restart tests to CI. The only provider behavior change bounds optional drafts to 256 tokens. No source agent branch is edited. `evaluation/models.json` records free public model choices; `evaluation/retail_rag_fixture.json` is labelled synthetic and cannot stand in for the user's operational data. Measured results are tracked in docs/integration/VALIDATION.md.

Final validation evidence: `8d0d2b444a6cc3382f11bc3720000e7c93ba1f26`, successful Actions run 35909119561. 178 tests pass; graph now 512 nodes / 809 edges. Runtime inputs and retrieval labels used only synthetic records. M13 remains incomplete for real-data validation under dataset requirements; no main merge is authorized.

## Interactive showcase extension

- [x] Responsive same-origin dashboard connected to authenticated inventory, analytics, forecast, chat, feedback and audit APIs.
- [x] Opt-in, localhost-only temporary synthetic database; normal operational startup remains empty.
- [x] Windows launch and presentation guide: [DASHBOARD.md](docs/integration/DASHBOARD.md).
- [x] Full local Python suite: 180 passed; source-preservation guard passed.
- [ ] Real dataset mapping and business validation (unchanged M13 requirement).


## Seasonal anomaly supplement

SEASONAL_RESULTS.json records fixed implementation e384d6c on April 1-May 26 development validation, with training ending March 31. STL weekly residuals, Isolation Forest and median deviation each detected all five large mixed-sign injections (AUROC/AP/F1 1.0; confusion 51/0/0/5; clean alert rate 0). This easy proxy shows no superiority of STL over simpler methods. It is not natural anomaly accuracy, independent final-test evidence or a false-positive-rate estimate. The original RESULTS.json remains untouched. No tuning, model promotion or production wiring occurred.

Tests verify that changing validation values cannot change any training threshold, source arrays remain unchanged, missing days are rejected, and later dates cannot enter the supplement. Nine focused auxiliary tests pass. See SEASONAL_PROTOCOL.md for reproduction scope and assumptions.


## Expanded retrieval development fixture

Frozen implementation 72282a4 measured 50 authored positives and 15 negatives over ten fictional policy documents using a local TF-IDF baseline and the unchanged signed RAG pipeline. Recall@1 0.98, Recall@3 1.00, MRR@3 0.99, nDCG@3 0.9926. All 15 negatives abstained, but only 17/50 positives returned evidence: abstention precision is 0.3125. Strong raw retrieval does not establish usable answer coverage. No thresholds or labels were changed after observing these results. No scope leaks were observed with the forbidden-store decoy. These labels are NOT human-reviewed and are not actual retail policy.

The first run wrote complete results but exited with a Windows file-lock cleanup error. The evaluator now explicitly closes the Chroma client before temporary-directory cleanup; a focused lifecycle test verifies removal after an indexed document. Frozen metrics were preserved and were not rerun to conceal failures. Automatic approval review rejected a later cleanup command as blocked by policy, so the original temporary artifact was left alone. See RAG_RESULTS.json, RAG_FIXTURE.json and RAG_PROTOCOL.md. No model download, external request or production wiring.


## Router review preparation

ROUTER_REVIEW.json contains 200 draft-labelled cases across all ten intents, organized into 100 paired groups kept together in deterministic partitions. Human review fields are blank. The reviewed-evaluation mode rejects missing review fields and insufficient case counts; the agent has not certified its own labels.

Frozen rule diagnostic at e3b60f8: accuracy 0.51, ten-label macro-F1 0.5871, 116 abstentions. A separate courtesy sentence ("Please.") is treated as an unsupported clause by the existing conservative router and drives many abstentions. This finding is preserved, not hidden by editing queries, labels or thresholds after evaluation. Some semantic labels also need human adjudication. Neither these authored queries nor the split names establish natural-query or independent test accuracy. The original protected source implementation is unchanged. Confidence remains a heuristic, not a calibrated probability.

Run `python -m scripts.evaluate_auxiliary_router`; frozen draft output refuses overwrite. After actual human review, `--reviewed` writes separate evidence. See ROUTER_PROTOCOL.md. This prepares a concrete review queue while retaining the human-review acceptance gate.


## Descriptive price association supplement

Owned additions: app/auxiliary/price.py, scripts/evaluate_price_association.py, tests/auxiliary/test_price.py and docs/auxiliary/PRICE_PROTOCOL.md. Frozen before measurement: training-only SKU/day log-price association with SKU/weekday controls and calendar trend, week-cluster uncertainty. Missing dates remain absent, no test labels are read, no pricing action or causal elasticity claim. Three focused checks pass (coefficient recovery, rank/missingness behavior and invalid/test-period input rejection). Measurement pending.


## Measured price association (development only)

Frozen implementation 7356baec0a120c11b3b5b9354f569e5b16672eb6 read 12,862 positive observed SKU/day aggregates for 85 products, September 29-March 31, across 27 week clusters. The log-price association coefficient is -0.2484 with a week-cluster 95% t interval [-0.3862, -0.1106] (26 degrees of freedom). SKU, weekday and linear calendar trend controls do not remove stock, promotion, exposure, selection or price/quantity coupling. This is synthetic descriptive evidence, not causal elasticity or a price recommendation. Missing dates were left absent. No final-test labels or existing frozen metrics were reread or altered. PRICE_RESULTS.json records versions and source digest; PRICE_PROTOCOL.md documents assumptions.

The installed statsmodels emits pandas deprecation warnings; execution succeeds with the pinned versions. No dependency upgrade was introduced. Human causal identification and real-data validation remain open.

Price supplement regression: 232 passed in 22.48 seconds (69 dependency deprecation warnings). Owned-path check found no changes to inherited app, scripts or tests outside auxiliary scope.


## Product ranking agreement supplement

Owned additions: app/auxiliary/similarity.py, scripts/evaluate_similarity.py, focused tests and SIMILARITY_PROTOCOL.md. Fixed training-only standardized features compare Euclidean and cosine full rankings/top-five overlap. Review fields stay blank; agreement between algorithms is not human relevance accuracy. Two focused tests cover deterministic ranks, self exclusion, label blanks, invalid input and missing-direction/short-history exclusions. Measurement pending.


## Measured geometric ranking agreement

Frozen implementation 1699a0139435ae826e2c0f54f6940c203e1437cc compared 85 training-period products. Mean top-five overlap is 0.743529 and full-ranking Spearman is 0.795624. No product was excluded for short history or zero direction. SIMILARITY_RESULTS.json includes 534 directed candidate pairs with blank human review fields. These values measure agreement between two geometric methods, not semantic relevance, customer substitution, or human ranking agreement. No final-test labels, runtime behavior or production similarity code changed. Independent judged relevance remains an acceptance gate.

Similarity supplement regression: 234 passed in 34.01 seconds (69 existing dependency deprecation warnings). Source-scope inspection confirms only owned auxiliary code/scripts/tests changed relative to the showcase base.
