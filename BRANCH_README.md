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
