# Conversational RetailOps development graph

Repository: Ashproxx/Retail_Operations (user clarification, 2026-09-28).
Baseline: b74a06df9753e7e20f66c4c6bb8874114fe50a9f, preserved at baseline/conversational-intelligence.
The PDF's Retail_Ops / codex baseline reference is superseded by the user's repository choice.

## Existing verified system

app/main.py -> app/integration/routes.py -> authenticated Runtime -> LangGraph Orchestrator -> eight domain adapters -> authorized Repository -> SQL.
RAG: SignedRag -> Chroma + local sentence-transformers -> signed manifest. AuditChain and scoped 24-hour memory remain in place.
Prior dashboard: app/dashboard/static -> authenticated API. Baseline limitations addressed by the new `/assistant` workspace: hard-coded showcase choices, explicit SKU/date forms, narrow follow-ups, baseline-only forecasting, no conversational chart selection.
Existing full index: docs/knowledge_graph/MASTER_KNOWLEDGE_GRAPH.json on the baseline (528 nodes / 846 edges).

## Implemented conversational flow

Conversation UI -> conversational API -> scope-aware dimension discovery -> natural-language router -> progressive clarification -> typed context -> deterministic analytics / inventory / forecast / competition -> grounded synthesis -> structured charts -> optional RAG policy evidence -> audit.

Business numbers always come from database tools. Product/location options are authorized database values. Unknown fields stay null. The prior operational API and RAG are retained for compatibility.

See project_graph.json, INTERFACES.md, DATA_DICTIONARY.md and BRANCH_REGISTRY.md for ownership and contracts. Milestones must be verified end to end before completion credit.

`app/conversation/routes.py` provides the authenticated API and same-origin `/assistant` mount. `app/conversation/static` renders local ECharts and accessible data tables. `showcase.py` supplies disposable labelled current-date fixtures. `tests/conversation` and `scripts/check_conversation.cjs` exercise the composed system. Original agents and RAG remain byte-preserved and guarded by `scripts/check_branch_scope.py`.

2026-09-30 knowledge delta: Windows timezone dependency declared; source guard uses Git-cleaned hashes; browser token parsing accepts CRLF; duplicate style names route to product choice; diagnostics expose category/store peers. Local suite: 201 passed. Both browser gates passed. Final remote gate passed: CI 36731448837; see VALIDATION.md.

## Phase 3 plan (2026-10-03)

Baseline f81bce0 is preserved. Root selector -> RetailOperations + Employee360. EmployeeWorkEfficiency and ManagementIntelligence are informational Coming Soon pages only. New SQL tables import the two supplied synthetic workbooks once; runtime queries never reopen Excel. Shared Store links Sales, Products, CompetitorSales, Employees and StoreStaffing. Employee -> Manager and Department; no employee-to-sale attribution.

Reuse authentication, scoped session storage, audit hash chain, taxonomy, chart renderer and forecasting candidates. Retail transactions use net_amount_inr, never fabricated stock. Employee responses are server-redacted by role before serialization and log field names, not sensitive values. No new cloud dependency.

Phase 3 sales checkpoint: imports -> indexed Sales/Product/CompetitorSale/StoreMetadata/ImportBatch; actual workbook imported; net source amounts verified and no inventory created.

Employee import checkpoint: shared stores -> employees/search_name + store_staffing; 150 supplied records imported; optional ratings stay null. HR access control is the next dependency.

HR security checkpoint: server grants -> role/store filter -> allowlisted profile -> audit field names. HR scopes do not grant retail permissions.

Retail Model 1 checkpoint: scoped SQL -> net sales/groups + distinct-order delivery + weekly competitor estimates + reused forecast backtests -> structured charts. Retail memory is phase3:retail; HR questions route to Employee360.

Employee360 checkpoint: authorized Employee rows -> name resolver/clarification -> redacted profile + staffing aggregates -> namespaced memory -> field-only audit. Cross-domain prompts route to the corresponding workspace.
