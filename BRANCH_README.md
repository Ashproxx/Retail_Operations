# integration/release-candidate

Base: foundation/core-platform `77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045`.
Human explicitly approved the exact sources in `docs/integration/APPROVED_SOURCES.json`, including security `e55f640b416d2109bac8fbf9dea2622dbdc78577`. Approval covers this candidate only; no main merge is authorized.

M13: INCOMPLETE. Official weighted completion: 95% (M0-M12 passed). All available local integration work is implemented. Real data/model validation and container/remote-CI execution remain unverified; no automatic milestone credit is awarded for configuration files alone.

## Scope and interfaces

Preserve source agent/router/RAG/security files byte-for-byte. Integrate through `app/integration`: registry, parameter bridge, LangGraph orchestration, authenticated routes, atomic CSV/XLSX loader, SQL repository, signed retrieval wrapper, local provider protocol, owned memory/feedback and CLI/demo.

SHARED DELTA: API registration in app/main.py, shared dependencies/env settings, tests/foundation route expectations, branch guard, Docker/CI and global integrated docs/graphs. Original metadata is archived by source branch under docs/integration/sources. Source branch refs are not modified.

Dependencies: existing LangGraph/Chroma/sentence-transformers branch requirements are installed centrally; existing httpx test dependency is now used by the local Ollama adapter. openpyxl (>=3.1,<4) is the only additional functional library, required for XLSX reading; CSV uses the standard library. CPU PyTorch is installed first to avoid unnecessary CUDA dependencies. No paid provider required.

SQL stores validated domain payloads keyed by immutable observation identity, plus store names, session state, request receipts/feedback and signed manifests. This is an explicit schema adapter pending actual production column inspection, not a fabricated business database. See README for source-to-field mappings and per-agent schema export.

## Validation and limitations

Run `python -m pytest -q`, `python scripts/check_branch_scope.py`, `python -m app.integration.demo` and `python -m pip check`. Latest results: docs/integration/REPORT.md. Uvicorn startup/health/OpenAPI are verified separately. Token provisioning is tested without printing secrets.

No live retail dataset, trained semantic evaluation or live Ollama model was provided. Docker is unavailable in the execution environment. CI configuration is present, but no remote run success is claimed. Role/store checks precede reads; audit is single-writer with independent anchors required across restarts. Natural-language rules are bounded; unsupported/missing parameters escalate. Numerical confidence is not calibrated. No production transactions or notifications are executed. Full limitations and setup are in README and ARCHITECTURE.md.

Published implementation: `1b50c1ea9e4a116cc5da04ba9df6efb2e46b9f0c`. Fetched tree matches the tested local tree. Full suite: 178 passed, 0 failed, 0 skipped. Graph: 500 nodes / 786 edges. All fourteen pre-existing refs verified unchanged. Final documentation SHA is recorded in the session response.
