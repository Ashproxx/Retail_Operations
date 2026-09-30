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

2026-09-30 knowledge delta: Windows timezone dependency declared; source guard uses Git-cleaned hashes; browser token parsing accepts CRLF; duplicate style names route to product choice; diagnostics expose category/store peers. Local suite: 201 passed. Both browser gates passed. Updated remote gate pending; see VALIDATION.md.
