# M2 router delta

Base: foundation/core-platform at 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045. Global graphs remain inherited snapshots; this branch graph records implemented router code only.

```mermaid
flowchart TD
    request[Query and trusted context] --> check[Validate session]
    check --> classify[Classify clauses and infer dependencies]
    classify --> gate{Confident and supported}
    gate -->|Yes| plan[Ordered typed handoff plan]
    gate -->|No| escalate[Human clarification]
    plan --> audit[Metadata audit and result]
    escalate --> audit
    audit --> sink[Optional private JSONL sink]
```

LangGraph implements the conditional transition. No task is executed; no RAG or domain branch is integrated. Produced interfaces: RouterAgent, RoutingPlan, Task, Intent, RouteSettings and JsonlAuditSink. Foundation interfaces are consumed unchanged.

27 router cases plus 20 foundation cases pass. Demo covers inventory, multi-intent inventory/demand/pricing and escalation. Confidence is heuristic; real-world semantic accuracy remains unevaluated. Security/authorization, downstream invocation and aggregate answers are separate dependencies. No SHARED DELTA.

M2 local PASS, remote publication pending. Previous completed milestones M0+M1+M11 total 23%; verified M2 adds 8% for 31%.
