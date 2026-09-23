# Branch README

Branch: agent/inventory
Parent/base: foundation/core-platform / 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045
Milestone: M3 PASS
Official completion: 40% (only remotely verified passed milestones)
Owner scope: app/agents/inventory/*, tests/inventory/*, branch metadata and knowledge delta
Human approval: continuation authorized; no integration or main merge approved

## Purpose and source-defined responsibilities
Latest-as-of stock snapshots, low stock, reorder-point comparison, lead-time stockout risk, safety stock, inventory position, reorder quantities, net stock movement, overstock, store/SKU filters and cross-store totals. AllocationStrategy and BayesianDemandStrategy protocols prepare future multi-echelon/game-theory extensions.

## Allowed file scope
Only the domain paths above and four branch metadata files. No SHARED DELTA. Inherited foundation/global documentation is unchanged.

## Interfaces consumed
Foundation Pydantic Contract, BaseAgent, QueryRequest, RequestContext, AgentResult, AuditEvent, Role and common errors, as used in source. No agent branch imports or integrations.

## Interfaces produced
Query, validated domain records, evaluate(records, query), Agent(BaseAgent).
Agent.run expects QueryRequest.message containing JSON matching domain.Query. This explicit structured adapter avoids pretending natural-language interpretation is integrated. Constructor validates and copies records. Non-admin callers are restricted to trusted context.store_ids before analysis; a requested store outside that scope escalates. This is not a replacement for the later security policy. Audit metadata records actual tool/agent calls, no raw query. Confidence remains zero until calibrated; computational output and assumptions are explicit.

## Deliverables
Latest-as-of stock snapshots, low stock, reorder-point comparison, lead-time stockout risk, safety stock, inventory position, reorder quantities, net stock movement, overstock, store/SKU filters and cross-store totals. AllocationStrategy and BayesianDemandStrategy protocols prepare future multi-echelon/game-theory extensions.
Branch graph/checklist, scope guard, executable demo and domain tests are included.

## Tests and reproduction
Python 3.11+; validated on 3.12. Install existing foundation requirements-dev.txt. No new runtime dependencies.

```bash
python -m pytest -q
python -m app.agents.inventory.demo
python -m app.agents.inventory.check_scope
python -m compileall -q app/agents/inventory
```

31 tests passed, 0 failed, 0 skipped, including 20 inherited foundation tests. One inherited Starlette/httpx deprecation warning. Demo, imports, graph consistency, scope and whitespace checks passed. These are branch-local tests, not integrated end-to-end tests. Tests use synthetic fixtures and temporary files, never production records.

## Knowledge graph changes
Machine-readable graph records 33 nodes and 38 ownership/definition/import/test edges. Master graph remains unchanged. Branch Markdown records data flow and interface ownership.

## Data dependencies
No real retail data supplied. All demos are marked fixture=True. Empty repositories return missing/insufficient-data results rather than synthetic answers. Real sources require an approved loader/mapping and data authorization during integration.

## Known limitations and assumptions
Safety stock assumes independent daily demand and fixed lead time: z*sigma*sqrt(lead days). Demand-based target covers lead+review days. Missing demand produces null risk/quantity; missing variability is warned and omitted. On-order timing is unknown and not used to claim immediate availability. Explicit as_of and age_days expose snapshot staleness. Latest valid snapshot selected per store/SKU; duplicate dates rejected. No real-time connector, Bayesian solver or multi-echelon optimizer implemented.
No production accuracy claims. No API route registration, external calls, paid service or cross-branch merge. No credentials in source. No new dependencies needed beyond the foundation libraries and Python standard library.

## Cross-branch dependencies
Shared loader, router/API wiring and other agent outputs remain explicit integration dependencies. No changes from another development branch were copied, merged, rebased or cherry-picked. Domain interfaces remain independent until human-approved integration.

## Security considerations
Validate structured input; use trusted RequestContext; never treat JSON role claims as authority. Private data and keys must stay out of git. Returned results may contain source information and must be access-controlled by the integration layer. Statistical or risk recommendations are advisory; no operational writes occur.

## Last validated commit and remote savepoint
Pinned base: 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045. Verified implementation savepoint: d28f3016222311454fd7adeccb32b4c72d90eabe. Final documentation commit is recorded in the session report. No self-referential commit hash is required.

## Latest status and previously verified branches
- M0: context/project-knowledge @ 3cc1a8df36c49147daac2c3967f37020bb0f5654 (5%)
- M1: foundation/core-platform @ 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045 (10%)
- M11: platform/agentic-rag @ e3638225a5ea88ab6036ce6148f66d9208cedf5c (8%)
- M2: agent/router @ 034946159557d9e88e2cd591b284f370fa6a9831 (8%)

## Next tasks
Publish Inventory, then implement Demand Forecasting and Analytics on separate branches from the pinned foundation.
Integration requires explicit approval of exact branches/commits; main remains human-controlled.
