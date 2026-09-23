# Proposed M13 integration — HUMAN APPROVAL REQUIRED

This is a review manifest only. No integration branch exists or is modified by this proposal.

Proposed base: foundation/core-platform @ 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045.
Proposed target: integration/release-candidate. Never main.

## Verified sources

| Milestone | Branch | Pinned commit | Weight |
|---|---|---|---:|
| M0 | context/project-knowledge | 3cc1a8df36c49147daac2c3967f37020bb0f5654 | 5% |
| M1 | foundation/core-platform | 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045 | 10% |
| M2 | agent/router | 034946159557d9e88e2cd591b284f370fa6a9831 | 8% |
| M3 | agent/inventory | bc1a4d5c1a3c62e81512b0b9cdbc6eceaa58d3ba | 9% |
| M4 | agent/order-fulfillment | 21acc0898ce8b3f0f130bb21b8b4b2fbafc7851b | 7% |
| M5 | agent/supply-chain | bce3f17d4798e121a4c8f3aa1e697b093ab47e0d | 8% |
| M6 | agent/pricing-promotions | 57ff09d09ad74eb623d28168b63774df25ea3294 | 8% |
| M7 | agent/customer-service | 5ecdbf6eab71715657b1a17e1305ab6702b8704d | 6% |
| M8 | agent/returns-refunds | 4a0b17d7d071e9cb203ccf3f5b6474e5d5eb61bb | 6% |
| M9 | agent/demand-forecasting | 7a65d8dab39697ef62be14e5feda945efda55ac9 | 8% |
| M10 | agent/analytics-reporting | 26f58b0600e6df6c8a37523ebff2065f6705d73b | 7% |
| M11 | platform/agentic-rag | e3638225a5ea88ab6036ce6148f66d9208cedf5c | 8% |
| M12 | security/privacy-integrity | 15bdd6eb73f1564a950f167ca1f20fbea09f9f0f (implementation savepoint; final reviewed documentation commit shown in session report) | 5% |


M0 is inherited through the foundation; do not separately merge it. Merge only specifically approved source commits into the candidate. Preserve source-branch README/checklists/graphs under a branch-specific archive during metadata conflict resolution; build one accurate integrated architecture/knowledge graph in the candidate. Agent IDs differ between some domain adapters and router plan targets; use an explicit registry mapping and verify output provenance.

## Remaining work to meet the full project prompt

The milestone percentage measures isolated branch exit criteria; it is not a runnable integrated product percentage. Before M13 can PASS:

1. Wire the router plans to all authorized domain agents, RAG, aggregation/conflict resolution and human escalation. Bridge structured JSON adapters to natural-language query parameters and test failures; no silent guessed IDs or dates.
2. Complete approved CSV/XLSX schema mapping/validation and persistent retail database ingestion. No actual retail dataset has been supplied; do not fabricate production tables or business results. Clearly labelled fixtures may support integration tests only.
3. Connect a local Ollama provider abstraction and deterministic test provider; keep hosted/Azure provider seams explicit. Pretrained semantic embedding quality still needs approved local model weights and a labelled retail evidence set.
4. Register required APIs, trusted authentication, RBAC before all access, signed retrieval manifests, durable audit, lightweight scoped session memory and feedback capture.
5. Add Docker development support, CI and integrated setup/API documentation on the approved integration/shared scope; validate startup, single/multi-agent queries, follow-up queries, conflict/error paths and complete QA. CI must not require paid credentials or mutate branches.
6. Record any unavailable external model/data/connector requirements honestly. M13 remains INCOMPLETE while required end-to-end gates fail. Azure deployment remains later work, as requested.

The human must approve M13 integration and these exact source commits (plus the final security documentation SHA) before work begins. Approval of integration is not approval to merge into main. No merge, force push, history rewrite or branch deletion has been performed.
