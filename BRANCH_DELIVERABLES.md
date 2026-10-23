# M18 auxiliary evaluations - measured partial checkpoint

Branch ml/auxiliary-models, based on showcase c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. No cross-branch merge, runtime hook or protected-branch change.

Measured results: docs/auxiliary/VALIDATION.md and RESULTS.json. Delivery candidates have worse Brier scores than the prevalence baseline; no promotion. Clustering is descriptive; anomaly metrics apply only to five large injected spikes. M18 remains partial.

Scope: app/auxiliary, tests/auxiliary, scripts/evaluate_auxiliary.py, scripts/evaluate_seasonal_anomalies.py, requirements-auxiliary.txt, docs/auxiliary and these branch records. Read-only local CLI; results contain aggregate metrics, no customer/employee records. Dependencies are already installed and pinned separately.

Fixed protocol before first test evaluation: delivery models train on resolved delivered orders sold and resolved by March 31; validation April 1-August 4, test August 5-September 29. Labels must be resolved by each partition end. No tuning or refitting. Logistic C=1 and forest 100 trees/depth 8/min-leaf 20 compare with training prevalence. Threshold .5. Preprocessors fit only training rows; each order counted once; conflicting lines excluded. Record ROC-AUC, average precision, Brier, calibration bins, ECE and confusion matrices. Missing outcome labels are not negatives.

Segmentation: train-period observed product features, fixed k=3 and seed 42; report descriptive in-sample silhouette, not held-out accuracy. Anomalies: train-period daily counts; five seeded upward spikes in a copy of the 56-day test block; fixed IsolationForest versus median-absolute-deviation baseline, thresholds from training 95th percentile. No natural anomaly labels, no false-positive-rate claim. This separate proxy task does not retune M17 forecasting.

Pending/unverified: human-reviewed router labels, expanded signed-RAG benchmark, independent natural-anomaly validation, similarity ranking agreement, price-effect uncertainty and stockout labels. No acceptance or real-world performance claim before measurement. M20 requires exact-commit approval.

---

## Inherited branch record

# Integration deliverables

Current Phase 3 deliverables: [development report](docs/phase3/VALIDATION.md) and [hard milestone ledger](docs/phase3/MILESTONES.md). Source SQL importers, separate retail/HR services, HR permissions, four-model selector and responsive website are implemented. Main merge requires explicit final authorization. Historical M13 below describes the earlier release only.

## Historical release candidate

M13 INCOMPLETE; weighted completion remains 95%.

- [x] Explicit approval recorded with pinned sources/base
- [x] Candidate created from approved foundation
- [x] Approved source commits integrated; source implementations preserved
- [x] Original metadata archived by branch
- [x] Authenticated API and explicit role/store checks before reads
- [x] All eight domain agents wired through LangGraph and registry
- [x] Multi-agent aggregation, conflict escalation and bounded execution
- [x] Conservative natural-language parameter bridge and scoped follow-up memory
- [x] Atomic CSV/XLSX ingestion with validation and fixture provenance
- [x] Persistent SQL records, owned feedback, durable audit chain
- [x] Real Chroma/local-embedding tests and signed-manifest rejection
- [x] Ollama protocol adapter and tested deterministic failure fallback
- [x] Full available automated suite and live Uvicorn startup verification
- [x] Docker and read-only CI configurations
- [x] Setup/API/data/architecture documentation and regenerated graphs
- [x] Source-preservation/ancestry scope guard
- [x] Candidate implementation pushed and fetched; file tree/ancestry verified
- [x] All fourteen pre-existing branch refs, including main, verified unchanged
- [x] Live Ollama smoke test with an installed model (SmolLM2 135M)
- [x] Pinned pretrained embeddings and labelled synthetic retrieval evaluation (MiniLM, 12 positive / 2 negative queries)
- [ ] Real retail dataset mapping and end-to-end validation
- [x] Previous remote CI and Docker image build verified (run 35878697558)
- [x] Expanded container runtime, real Ollama and pretrained retrieval checks verified (run 35909119561)
- [ ] M13 complete / eligible for final human review

Publication evidence and source/main ref checks are recorded in docs/integration/REPORT.md and the session report. No main merge is authorized.

## Interactive showcase extension

- [x] Responsive same-origin dashboard connected to authenticated inventory, analytics, forecast, chat, feedback and audit APIs.
- [x] Opt-in, localhost-only temporary synthetic database; normal operational startup remains empty.
- [x] Windows launch and presentation guide: [DASHBOARD.md](docs/integration/DASHBOARD.md).
- [x] Full local Python suite: 180 passed; source-preservation guard passed.
- [ ] Real dataset mapping and business validation (unchanged M13 requirement).

Measured checks: 7 auxiliary tests passed; full regression 221 passed in 23.20 seconds.


## Seasonal anomaly supplement

SEASONAL_RESULTS.json records fixed implementation e384d6c on April 1-May 26 development validation, with training ending March 31. STL weekly residuals, Isolation Forest and median deviation each detected all five large mixed-sign injections (AUROC/AP/F1 1.0; confusion 51/0/0/5; clean alert rate 0). This easy proxy shows no superiority of STL over simpler methods. It is not natural anomaly accuracy, independent final-test evidence or a false-positive-rate estimate. The original RESULTS.json remains untouched. No tuning, model promotion or production wiring occurred.

Tests verify that changing validation values cannot change any training threshold, source arrays remain unchanged, missing days are rejected, and later dates cannot enter the supplement. Nine focused auxiliary tests pass. See SEASONAL_PROTOCOL.md for reproduction scope and assumptions.
