# Branch README

Branch: foundation/core-platform
Parent branch / base commit: context/project-knowledge / 3cc1a8df36c49147daac2c3967f37020bb0f5654
Milestone: M1 PASS; official project completion 15% (M0 5% + M1 10%)
Owner scope: shared configuration, schemas, database abstractions, API skeleton, common errors, logging, contracts and foundation tests
Human approval status: user approved the exact context base on 2026-09-23; no integration or main merge authorized

## Purpose
Provide the shared foundation for isolated agent, RAG and security branches. The inherited master graph and governance files are the M0 snapshot; this branch delta is authoritative for M1 status.

## Source-defined responsibilities
Preserve FastAPI and the planned LangGraph, ChromaDB, sentence-transformers and Ollama architecture. Azure deployment remains later work. M1 installs only dependencies used by the foundation.

## Allowed file scope
app/*; tests/foundation/*; requirements*.txt; pyproject.toml; .env.example; .gitignore; scripts/check_branch_scope.py; branch README/checklist and branch knowledge delta. No master/context files updated. No SHARED DELTA.

## Interfaces consumed
Approved M0 design and interface registry. No actual business dataset or policy sources are available.

## Interfaces produced
- Settings: RETAILOPS_ environment variables and .env loading, validated confidence/iteration limits, redacted database URL.
- QueryRequest: message and session_id only. Roles/principal are excluded from client input.
- RequestContext: internal principal, role, scoped stores and request/session IDs; not an authentication implementation.
- BaseAgent.run(QueryRequest, RequestContext): async AgentResult including provenance, confidence, warnings, handoffs and timing.
- AgentResult, ChatResponse, Evidence, AuditEvent and ErrorResponse: typed schemas with independent collection defaults.
- Database.session(): commit/rollback/close lifecycle through SQLAlchemy; Database.ping() and close().
- DatasetLoader.load(path, column_mapping): abstract CSV/XLSX load contract and source-file validation. No ingestion implementation yet.
- RetailRepository: abstract observed-stock and store-inventory lookup. Missing data is None/empty; no generated business values.
- GET / identifies foundation stage; GET /health probes the database and returns 200 or sanitized 503. GET /docs and /openapi.json are available.

## Deliverables
Modular package, install metadata, configuration, environment example, logging, exceptions, schemas, contracts, SQLAlchemy lifecycle, FastAPI factory/lifespan, tests and branch scope guard.

## Dependencies and decisions
No existing requirements were available to reuse. FastAPI provides the requested API/OpenAPI; Pydantic validates contracts; pydantic-settings loads environment/.env; SQLAlchemy keeps a future PostgreSQL migration path; Uvicorn runs the ASGI server. pytest and httpx are test-only dependencies. No cloud keys, model downloads or paid API calls are needed. Versions are major constrained; this is not a production lockfile.
SQLite in memory is the default for safe local setup; set RETAILOPS_DATABASE_URL=sqlite+pysqlite:///./retailops.db for persistence. Domain models wait for actual column inspection. Use a trusted authentication adapter before deploying domain routes. Do not expose raw SQL as an API.

## Setup and run
Python 3.11+ (validated with 3.12). From repository root:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
# Optional: copy .env.example to .env and edit it
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/health and http://127.0.0.1:8000/docs.

## Tests
```bash
python -m pytest -q
python scripts/check_branch_scope.py
python -m compileall -q app
```
20 passed, 0 failed, 0 skipped. Third-party warnings: Starlette deprecates httpx TestClient integration and an AnyIO BlockingPortal alias. They do not affect these passing tests; dependency compatibility needs continued monitoring. ASGI startup, database health and OpenAPI exercised with lifespan-enabled TestClient. Live Uvicorn smoke check recorded in the session report.

## Knowledge graph changes
Branch delta maps foundation files, Python imports, endpoints, contracts, tests and ownership. Master graph remains unchanged on its context branch.

## Data dependencies
No retail data supplied. Test fixtures are synthetic, in temporary databases only. No CSV/XLSX parser or business data migration is claimed.

## Known limitations
No domain agents, LangGraph execution, RAG, embedding models, LLM provider implementation, authentication/RBAC enforcement, durable audit storage, conversation memory, Docker or CI yet. /api/chat and other domain routes intentionally remain unregistered. Metadata logging excludes payloads, raw errors and credentials but is not a tamper-evident audit implementation. M1 does not constitute a deployed production API.

## Cross-branch dependencies
Subsequent agent/platform/security branches must start from the pinned published foundation commit. All consume these contracts. No merge/cherry-pick/rebase occurred; integration requires separate explicit approval.

## Security considerations
Input validation, server-generated request IDs, no raw exception responses, metadata-only logs, hidden SQL parameters and secret-redacted configuration. Environment values and local databases are ignored. Role definitions are a contract, not an authorization grant.

## Last validated commit
Approved base 3cc1a8df36c49147daac2c3967f37020bb0f5654. Validation applies to this commit's source tree; the final remote SHA is recorded in the session report.

## Latest test result
20 passed, 0 failed, 0 skipped; compile, branch scope, dependency, graph and live startup checks PASS. Implementation savepoint a9a8df42e84a7eff3950cee94b4a5a2760de0c4c published and verified remotely. Main remains c21658e55c96d7adc78b82d2e2f3d2b17d226144 and context remains the approved base.

## Next tasks
Pin verified M1 commit; begin platform/agentic-rag on its own branch; then router and inventory branches. Obtain actual CSV/XLSX and policy data before claiming production grounding. No integration is authorized.
