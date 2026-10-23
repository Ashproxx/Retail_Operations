# M17 forecasting models — in progress

Active branch: ml/forecasting-models. Human-authorized dependency base: platform/ml-core@ca22a9f; permission to continue without routine confirmations was given on 2026-10-23. Main and integration/dual-model-retailops are untouched.

Checkpoint: Croston, SBA, TSB and Gamma–Poisson observed-count adapters; finite-sample split-conformal radius/bands, empirical interval coverage and pinball metrics. Seven focused ML tests pass (five inherited, two new). Missing dates are rejected; sparse workbook transactions are not relabelled as zero sales. Intervals require sufficient separate out-of-sample calibration residuals; nominal coverage is not a guarantee for dependent time-series data.

NOT COMPLETE: ETS/SARIMA/SARIMAX, linear/boosting models, independent holdout benchmarks, weather ablation, technique survey and comparisons remain to implement. No new model score or M17 completion is claimed. No dependency added at this checkpoint. Source code and tests only; no model weights or retail data sent externally.

---

## Inherited branch record

# M15 ML core

Branch: platform/ml-core. Base: integration/dual-model-retailops@c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. User approved work on all four addendum areas on 2026-10-23. M14 design is on docs/ml-methodology@e8f8280; no source-branch merge is performed.

Scope: app/ml, tests/ml, configs/ml_baseline.yaml, scripts/ml_run.py, scripts/ml_report.py, requirements-ml.txt and docs/ml. SHARED DELTA: add seven branch names to check_branch_scope.py, add isolated --ml-delta mode to update_knowledge_graph.py, ignore local experiment logs. No model download, new dependency or web-service change.

Implemented: cutoff-safe features and role-filtered SQL extraction; baseline protocol/adapter; numerical parity; expanding validation with horizon gap; metrics and block bootstrap; data-only baseline registry; seeded permutation importance; freshness/error/drift summaries; reproducible baseline command and honest scorecard. Future covariates await M16 data and M17 adapters. Every scorecard pillar remains UNVERIFIED for independent test performance.

Run `.venv/Scripts/python.exe -m scripts.ml_run --config configs/ml_baseline.yaml` then `python -m scripts.ml_report`. Config uses JSON syntax, a YAML subset, without another dependency. Source DB is local and required. Outputs contain validation evidence, not final-test scores. See docs/ml/CORE_VALIDATION.md for checks and limits. M20 integration remains human-gated.

---

## Inherited historical record

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
