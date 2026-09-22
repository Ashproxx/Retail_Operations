# File ownership

| Branch | Scope |
|---|---|
| context/project-knowledge | knowledge graph and governance |
| foundation/core-platform | configuration, schemas, database abstractions, FastAPI skeleton |
| agent/router | router implementation, tools, domain tests |
| agent/inventory | inventory implementation, tools, domain tests |
| agent/order-fulfillment | order-fulfillment implementation, tools, domain tests |
| agent/supply-chain | supply-chain implementation, tools, domain tests |
| agent/pricing-promotions | pricing-promotions implementation, tools, domain tests |
| agent/customer-service | customer-service implementation, tools, domain tests |
| agent/returns-refunds | returns-refunds implementation, tools, domain tests |
| agent/demand-forecasting | demand-forecasting implementation, tools, domain tests |
| agent/analytics-reporting | analytics-reporting implementation, tools, domain tests |
| platform/agentic-rag | ingestion, chunking, embeddings, retrieval, verification |
| security/privacy-integrity | RBAC, hashes, audit integrity |
| integration/release-candidate | approved integration and full QA |

Current branch owns docs/governance/*, docs/knowledge_graph/* and branch metadata only. Each later branch owns its own branch metadata and relevant tests. Shared file exceptions require a documented SHARED DELTA; none in M0. README.md remains unchanged.
