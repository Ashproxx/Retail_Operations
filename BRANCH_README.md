# M18 auxiliary evaluations - measured partial checkpoint

Branch ml/auxiliary-models, based on showcase c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. No cross-branch merge, runtime hook or protected-branch change.

Measured results: docs/auxiliary/VALIDATION.md and RESULTS.json. Delivery candidates have worse Brier scores than the prevalence baseline; no promotion. Clustering is descriptive; anomaly metrics apply only to five large injected spikes. M18 remains partial.

Scope: app/auxiliary, tests/auxiliary, scripts/evaluate_auxiliary.py, scripts/evaluate_seasonal_anomalies.py, requirements-auxiliary.txt, docs/auxiliary and these branch records. Read-only local CLI; results contain aggregate metrics, no customer/employee records. Dependencies are already installed and pinned separately.

Fixed protocol before first test evaluation: delivery models train on resolved delivered orders sold and resolved by March 31; validation April 1-August 4, test August 5-September 29. Labels must be resolved by each partition end. No tuning or refitting. Logistic C=1 and forest 100 trees/depth 8/min-leaf 20 compare with training prevalence. Threshold .5. Preprocessors fit only training rows; each order counted once; conflicting lines excluded. Record ROC-AUC, average precision, Brier, calibration bins, ECE and confusion matrices. Missing outcome labels are not negatives.

Segmentation: train-period observed product features, fixed k=3 and seed 42; report descriptive in-sample silhouette, not held-out accuracy. Anomalies: train-period daily counts; five seeded upward spikes in a copy of the 56-day test block; fixed IsolationForest versus median-absolute-deviation baseline, thresholds from training 95th percentile. No natural anomaly labels, no false-positive-rate claim. This separate proxy task does not retune M17 forecasting.

Pending/unverified: human-reviewed router labels, expanded signed-RAG benchmark, independent natural-anomaly validation, similarity ranking agreement, price-effect uncertainty and stockout labels. No acceptance or real-world performance claim before measurement. M20 requires exact-commit approval.

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
