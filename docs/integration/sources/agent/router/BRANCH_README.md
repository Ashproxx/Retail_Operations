# Branch README

Branch: agent/router
Parent branch / base commit: foundation/core-platform / 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045
Milestone: M2 PASS; official completion 31% (M0 + M1 + M11 + M2)
Owner scope: routing, intent classification, planning, router audit and router tests
Human approval status: continuation authorized; no integration or main merge authorized

## Purpose
Implement the Router Agent on the pinned foundation, preserving isolation from RAG and other agents. Inherited global docs are M0 snapshots; this branch delta records current router implementation.

## Source-defined responsibilities
Classify queries, split multi-intent requests, sequence proposed domain handoffs, provide routing confidence, escalate uncertainty and record traceable decisions. This is a plan-only agent: downstream agents are not executed on this branch.

## Allowed file scope
app/orchestration/router/*, tests/router/* and branch metadata/knowledge delta. No SHARED DELTA. No changes to inherited foundation code, global docs, requirements or other branches.

## Interfaces consumed
BaseAgent, QueryRequest, RequestContext, AgentResult, AuditEvent, Settings, DataValidationError and foundation metadata logger. No imports from completed RAG branch.

## Interfaces produced
- RouterAgent.run(query, context): async AgentResult containing structured plan and audit metadata. Mismatched sessions raise DataValidationError.
- RouteSettings: confidence threshold (0,1], maximum agents [1,8]; default threshold derives from foundation environment settings.
- RoutingPlan: intent, candidates, heuristic confidence, human flag, reason, ordered Task objects, rule IDs and classifier version.
- Task: step ID, target domain/agent, prior-step dependencies, matched subqueries and reason codes.
- LangGraph RouterState: classify -> plan or escalate -> END. Graph state is transient; tracing disabled explicitly and no checkpointer used.
- JsonlAuditSink: optional local metadata-only audit persistence, with process-local locking; exceptions propagate if a configured sink fails. Store private audit files outside the repository. No tamper-proof/durable distributed audit claim.

## Deliverables
Eight domain classifications plus MULTI_AGENT/UNKNOWN, deterministic English rules, configurable confidence gate, conservative handling of alternatives/negation and unknown clauses, ordered multi-agent plan, request-linked audit, offline demo, branch scope guard and tests.

## Routing decisions and limitations
Specific domain expressions score 0.82, weak keywords 0.45 and inferred demand dependencies 0.75. Plan confidence is the lowest candidate score; unknown clauses, explicit alternatives/negation and some outside-retail terms cap it at 0.4 and force clarification. Scores are heuristic and not calibrated probabilities. Threshold tuning is not an accuracy result.

Repeated intents are deduplicated. Task ordering is analytics -> inventory -> demand -> supply chain -> order -> pricing -> returns -> support for the matched subset, with sequential dependencies. Future stock questions add demand, and explicit sales-drop causal questions may add demand. These are explainable baseline rules, not a learned optimizer. Compound subqueries may share a clause; full linguistic decomposition is not claimed. Only English rules are provided; paraphrases, punctuation, uncommon terms, mixed languages and subtle negation can still be misclassified. No entity extraction, conversational memory or production accuracy claim.

## Dependencies
app/orchestration/router/requirements.txt adds LangGraph for the required explicit state/branch workflow; foundation has no equivalent. LangSmith is already a LangGraph dependency and is declared directly because tracing_context is used to disable query export even when environment tracing is enabled. No hosted model, paid service or API key is used.

## Setup, demo and tests
From the repository root, in an activated Python 3.11+ virtual environment (tested with 3.12):

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -r app/orchestration/router/requirements.txt
python -m pytest -q
python -m app.orchestration.router.demo
python -m app.orchestration.router.check_scope
python -m compileall -q app/orchestration/router
```

For application use, instantiate RouterAgent and await run(QueryRequest(...), trusted_context). For opt-in audit persistence, pass audit_sink=JsonlAuditSink(Path('/private/path/router-audit.jsonl')). Provision that parent directory and appropriate filesystem permissions first. The FastAPI routes are unchanged; /api/chat is not registered.

## Tests
47 passed, 0 failed, 0 skipped (20 inherited foundation + 27 router cases). One third-party AnyIO BlockingPortal deprecation warning. Tests cover every domain, single/multi-intent plans, unknown and weak requests, confidence thresholds, negation, outside-retail requests, partly unsupported requests, agent limits, deduplication, forward-stock dependency, session mismatch, concurrent state isolation, audit privacy/persistence/failure and tracing suppression. Demo shows inventory, inventory+demand+pricing, and escalation.

## Knowledge graph changes
Branch graph maps router file ownership, imports, graph branches, tests, produced contracts and inherited dependencies. Master graph remains unchanged on the context branch.

## Data dependencies
No dataset required to classify the tested examples. No operational retail facts are generated. Demonstration principal and session are fixtures.

## Security considerations
Routing grants no authorization. Trusted context must come from a future security adapter. The router does not access business tools or execute user instructions. Returned task subqueries contain user text and must be handled as private input. Audit rows exclude raw query/documents; logger records reason code and request ID. Local JSONL audit is not tamper-evident and access controls/retention are deployment responsibilities. LangSmith tracing is disabled for graph invocation.

## Cross-branch dependencies
Execution of these tasks requires separately implemented agents and approved integration. Security must authorize each handoff. RAG remains on its own branch and was not imported or merged. Shared FastAPI registration and aggregation remain future approved integration work.

## Last validated commit
Pinned foundation base 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045. Final published SHA is recorded in the session report.

## Latest test result
47 tests and the demo PASS; compile, dependency, graph and scope checks PASS. Published implementation 244d971d40c85cc5e0330dd2c88afd83e5dd1d1c verified with git ls-remote. Official completion 31%. Other branch heads remain unchanged.

## Next tasks
Verify publication; create agent/inventory from pinned foundation; implement stock/reorder tools with tests and missing-data handling; evaluate router paraphrases against a labelled retail query set. Obtain the actual dataset before claiming real-data inventory results. Integration needs separate human approval.
