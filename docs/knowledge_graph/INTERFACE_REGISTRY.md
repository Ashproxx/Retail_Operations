# Planned interfaces — none implemented

| Interface | Owner | Contract |
|---|---|---|
| QueryRequest | foundation/core-platform | message, session_id, authenticated role/context, request_id |
| AgentResult / BaseAgent | foundation/core-platform | agent, request_id, status, summary, data, evidence, confidence, recommendations, warnings, handoffs, tool_calls, latency |
| ChatResponse | foundation/core-platform | session_id, agents_used, answer, data, sources, confidence |
| Database / DatasetLoader | foundation/core-platform | parameterized store/SKU/date queries; validated CSV/XLSX; explicit missing data |
| RoutingPlan | agent/router | ordered intents, confidence, human escalation below threshold |
| RetrievalResult | platform/agentic-rag | chunks, document/source IDs, hashes, auth tags, relevance, iterations, sufficiency |
| Authorization | security/privacy-integrity | trusted principal, action, resource; deny before tool/retrieval execution |
| AuditEvent | foundation/core-platform | request/session ID, timestamp, role, route, agents/tools/docs, iterations, confidence, latency, status |
| Integrity | security/privacy-integrity | canonical SHA-256 document verification and audit chain validation |
| LLMProvider | foundation/core-platform | local Ollama and deterministic testing; swappable hosted provider later |

Planned routes: GET /, GET /health, POST /api/chat, POST /api/query, POST /api/rag/ingest, GET /api/inventory/low-stock, GET /api/inventory/{store_id}, GET /api/analytics/summary, GET /api/audit, POST /api/forecast. Shared route registration belongs to foundation or approved integration. Endpoint role fields alone must not be trusted as authentication.
