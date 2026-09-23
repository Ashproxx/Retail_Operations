# Branch README

Branch: agent/customer-service
Parent/base: foundation/core-platform / 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045
Milestone: M7 PASS
Official completion: 84% (only remotely verified passed milestones)
Owner scope: app/agents/support/*, tests/support/*, branch metadata and knowledge delta
Human approval: continuation authorized; no integration or main merge approved

## Purpose and source-defined responsibilities
Evidence-grounded FAQ/policy excerpts, source metadata in AgentResult, validity/approval/store filters, content-hash checks, sentiment/complaint classification, domain handoff suggestions and explicit human escalation for absent or conflicting evidence. EvidenceRetriever protocol prepares later authorized RAG integration.

## Allowed file scope
Only the domain paths above and four branch metadata files. No SHARED DELTA. Inherited foundation/global documentation is unchanged.

## Interfaces consumed
Foundation Pydantic Contract, BaseAgent, QueryRequest, RequestContext, AgentResult, AuditEvent, Role and common errors, as used in source. No agent branch imports or integrations.

## Interfaces produced
Query, validated domain records, evaluate(records, query), Agent(BaseAgent).
Agent.run expects QueryRequest.message containing JSON matching domain.Query. This explicit structured adapter avoids pretending natural-language interpretation is integrated. Constructor validates and copies records. Non-admin callers are restricted to trusted context.store_ids before analysis; a requested store outside that scope escalates. This is not a replacement for the later security policy. Audit metadata records actual tool/agent calls, no raw query. Confidence remains zero until calibrated; computational output and assumptions are explicit.

## Deliverables
Evidence-grounded FAQ/policy excerpts, source metadata in AgentResult, validity/approval/store filters, content-hash checks, sentiment/complaint classification, domain handoff suggestions and explicit human escalation for absent or conflicting evidence. EvidenceRetriever protocol prepares later authorized RAG integration.
Branch graph/checklist, scope guard, executable demo and domain tests are included.

## Tests and reproduction
Python 3.11+; validated on 3.12. Install existing foundation requirements-dev.txt. No new runtime dependencies.

```bash
python -m pytest -q
python -m app.agents.support.demo
python -m app.agents.support.check_scope
python -m compileall -q app/agents/support
```

30 tests passed, 0 failed, 0 skipped, including 20 inherited foundation tests. One inherited Starlette/httpx deprecation warning. Demo, imports, graph consistency, scope and whitespace checks passed. These are branch-local tests, not integrated end-to-end tests. Tests use synthetic fixtures and temporary files, never production records.

## Knowledge graph changes
Machine-readable graph records 29 nodes and 34 ownership/definition/import/test edges. Master graph remains unchanged. Branch Markdown records data flow and interface ownership.

## Data dependencies
No real retail data supplied. All demos are marked fixture=True. Empty repositories return missing/insufficient-data results rather than synthetic answers. Real sources require an approved loader/mapping and data authorization during integration.

## Known limitations and assumptions
Local lexical evidence adapter only; ChromaDB integration is intentionally deferred across isolated branches. No generated policy text. Distinct relevant documents conservatively trigger conflict review even when potentially compatible. Sentiment and coverage are English heuristics, not learned or calibrated scores. Hashes must come from a trusted manifest and are unkeyed; stronger trust belongs to Security. No ticket is sent or created.
No production accuracy claims. No API route registration, external calls, paid service or cross-branch merge. No credentials in source. No new dependencies needed beyond the foundation libraries and Python standard library.

## Cross-branch dependencies
Shared loader, router/API wiring and other agent outputs remain explicit integration dependencies. No changes from another development branch were copied, merged, rebased or cherry-picked. Domain interfaces remain independent until human-approved integration.

## Security considerations
Validate structured input; use trusted RequestContext; never treat JSON role claims as authority. Private data and keys must stay out of git. Returned results may contain source information and must be access-controlled by the integration layer. Statistical or risk recommendations are advisory; no operational writes occur.

## Last validated commit and remote savepoint
Pinned base: 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045. Verified implementation savepoint: 1714eb47e8693df39774aa4ecd7f98afbc93d404. Final documentation commit is recorded in the session report. No self-referential commit hash is required.

## Latest status and previously verified branches
- M0: context/project-knowledge @ 3cc1a8df36c49147daac2c3967f37020bb0f5654 (5%)
- M1: foundation/core-platform @ 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045 (10%)
- M11: platform/agentic-rag @ e3638225a5ea88ab6036ce6148f66d9208cedf5c (8%)
- M2: agent/router @ 034946159557d9e88e2cd591b284f370fa6a9831 (8%)
- M3: agent/inventory @ bc1a4d5c1a3c62e81512b0b9cdbc6eceaa58d3ba (9%)
- M9: agent/demand-forecasting @ 7a65d8dab39697ef62be14e5feda945efda55ac9 (8%)
- M10: agent/analytics-reporting @ 26f58b0600e6df6c8a37523ebff2065f6705d73b (7%)
- M6: agent/pricing-promotions @ 57ff09d09ad74eb623d28168b63774df25ea3294 (8%)
- M5: agent/supply-chain @ bce3f17d4798e121a4c8f3aa1e697b093ab47e0d (8%)
- M4: agent/order-fulfillment @ 21acc0898ce8b3f0f130bb21b8b4b2fbafc7851b (7%)

## Next tasks
Publish Customer Service, implement Returns/Refunds, then privacy/security and prepare exact integration approval commits.
Integration requires explicit approval of exact branches/commits; main remains human-controlled.
