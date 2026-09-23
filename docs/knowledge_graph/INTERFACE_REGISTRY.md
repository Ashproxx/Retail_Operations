# Integrated interface registry

| Interface | Purpose |
|---|---|
| `ChatQuery`, `DirectQuery` | No client-controlled role; parameters validated by selected domain contract |
| `RequestContext` | Server-owned identity, role, store scope and request ID |
| `REGISTRY` / `contracts` | Router IDs -> domain classes and authorization actions |
| `Repository.records` | Authorized SQL record access before domain execution |
| `TabularLoader.load` | Explicit CSV/XLSX mapping and atomic record validation |
| `Orchestrator.run` | LangGraph dispatch, conflict handling, memory and audit |
| `SignedRag.query/ingest` | Trusted scope and HMAC manifest around the original vector store |
| `Provider.draft` | Optional unverified narrative; no tool execution authority |
| `AuditChain.append/read` | Metadata chain, single writer, externally retained anchor required |

Exact definitions are indexed in the machine-readable graph. Original branch contracts remain unchanged.
