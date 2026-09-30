# Conversational integration candidate

Branch: `integration/conversational-retailops`. Preserved baseline: b74a06df9753e7e20f66c4c6bb8874114fe50a9f. No `main` update or old agent branch rewrite.

Composition: taxonomy → calendar → scoped foundation → analytics/diagnostics → forecasting → competition → chart specs → conversational router → authenticated API/showcase → UI. Each feature has its own remote checkpoint and branch document. Corrections and cross-feature acceptance tests are owned here.

New entry points: `/assistant`, `POST /api/conversation`, `GET /api/conversation/options`, `python -m app.conversation.showcase`, `python -m app.conversation.ingest`.

Shared contracts: Pydantic `Turn` and server-owned `Context`; canonical observation records; chart specs; original registered agent contracts. API authentication remains the existing bearer-grant system. No operational write tool is added.

Integration corrections include progressive operational choices, compound intents, missing-category handling, comparison coverage by store, Product 360 dimensions, policy audit references, test-package isolation and current-date synthetic history.

Validation: original source guard; full Python suite; original and conversational real-browser flows; Docker build/config/start/restart; local Ollama; pinned retrieval evaluation. Exact measured runs and final gate status are in `docs/conversation/VALIDATION.md` and the milestone ledger.

Limitations: actual retail files were not supplied; no real-data accuracy or source mapping sign-off. External competition is unconfigured. Forecast intervals/similarity/diagnostic thresholds are explained heuristics. No Azure deployment or main merge. See the methods and run guides.

2026-09-30 checkpoint: verified 201 local tests and both browser gates. Corrected Windows timezone/CRLF portability, duplicate-name clarification and peer evidence. Reconciled milestone/feature records; updated remote CI pending. Latest published baseline verified: `299126c6c2e1c3a75d9f01b3f13e1bc364f5dd76`.
