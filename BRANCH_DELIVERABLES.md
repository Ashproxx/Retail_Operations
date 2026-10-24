# M17 forecasting models - measured checkpoint

Active branch: ml/forecasting-models. Authorized dependency base: platform/ml-core@ca22a9f. Main and integration/dual-model-retailops remain untouched.

Implemented: five inherited baselines; four observed-count methods; ETS, SARIMA and calendar SARIMAX; Ridge, Lasso and histogram boosting; tested forest and quantile adapters; separate conformal calibration. Optional dependencies are pinned in requirements-ml.txt. The frozen primary comparison covers 15 methods; forest and quantile adapters are not claimed as benchmarked.

Evidence: [measured comparison](docs/ml/MODEL_COMPARISON.md), [scorecard](docs/ml/AIML_SCORECARD.md), [technique survey](docs/ml/TECHNIQUE_SURVEY.md). Final test was opened once after configuration and two-block design were committed at c1e872f. Do not tune on or reopen this test as a fresh holdout. Full regression: 232 passed; focused ML suite: 18 passed.

Chain h=28 selected the weekday baseline before test: WAPE 13.5636%, versus histogram boosting 14.8524%, across 56 test observations. Empirical 80%/95% band coverage was only 67.86%/85.71%. Twelve series were eligible; 1,829 series were excluded without zero-filling. All 60 test fit/coverage failures are retained. Four candidates qualify for exploratory review; none is promoted.

M17 PARTIAL: time-safe weather/festival ablation, global pooled boosting, measured quantile comparison, expanded importance, real benchmark and independent review remain outstanding. M18/M19 have separate development branches; acceptance remains pending. M20 integration requires exact-commit approval. No source records or weights were sent externally.

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


## Pre-test quantile / importance supplement

At frozen code 4e17558, one chain h=14 origin (March 31, scoring April 15-28) measured .1/.5/.9 quantile pinball losses of 4.8149 / 9.7629 / 8.6392. No crossing occurred. Both quantile and baseline conformal 80% bands covered all 14 observations; mean widths were 134.54 and 139 units respectively. This tiny development validation window does not establish calibration or improvement; primary final-test undercoverage remains unchanged.

All eleven existing Poisson-boosting features have measured permutation MAE changes in QUANTILE_IMPORTANCE_RESULTS.json. They describe fixed recursive feature rows and correlated predictive associations, not causal importance or full rollout perturbations. Models never saw validation target labels during fitting or recursive feature generation. Existing final-test artifacts were neither reopened nor changed. Global pooling, broader independent comparisons, real benchmark and weather/festival-vintage evidence remain pending.


## Pooled boosting supplement protocol

Added app/ml/pooled.py and scripts/evaluate_pooled_forecasting.py with a fixed development comparison on 56 observed training days ending March 31, scoring April 15-28 after embargo. Shared boosting adds one-hot series identity and reuses existing past-only features/configuration. Local boosting and weekday baseline use identical training windows. Incomplete series are excluded, not zero-filled. Two tests verify recursion/history preservation, unknown-series rejection, common origins, gaps and later-date refusal. No primary-test rerun or runtime integration. See POOLED_PROTOCOL.md; measurement pending.


## Measured pooled forecasting supplement

Frozen implementation 22156f0 compared thirteen eligible stores on April 15-28 development data. Seven stores and all 120 store/category series were excluded for missing training/scoring dates, without zero-filling. Unweighted mean store WAPE: pooled boosting 40.1802%, local boosting 46.0297%, weekday baseline 40.2994%. Pooled boosting has lower WAPE than the baseline in only six of thirteen stores. This tiny mean difference is not evidence of superiority; no significance, promotion, calibrated pooled interval or independent final-test accuracy is claimed. Store/category pooling remains unverified due to coverage. POOLED_RESULTS.json records every per-store metric and exclusion. Existing primary evidence is unchanged.

Pooled supplement validation: full regression 236 passed in 22.71 seconds; source-preservation guard passed. Real benchmark, weather/festival-vintage ablation, independent review and integration remain pending.
