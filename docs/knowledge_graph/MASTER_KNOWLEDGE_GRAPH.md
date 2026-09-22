# Master knowledge graph

All diagrams describe the **planned** system; the baseline has no application code. Graph JSON distinguishes planned nodes from existing documentation.

## Overall architecture

```mermaid
flowchart TD
 user[User] --> api[FastAPI]
 api --> router[LangGraph router]
 router --> agents[Domain agents]
 agents --> tools[Structured tools]
 agents --> rag[Agentic RAG]
 tools --> db[Retail database]
 rag --> vector[ChromaDB]
```

## Multi-agent routing

```mermaid
flowchart TD
 query[Query] --> plan[Intent plan]
 plan --> confidence{Sufficient confidence}
 confidence -->|No| human[Human escalation]
 confidence -->|Yes| domains[Domain agents]
 domains --> aggregate[Conflict resolution and evidence aggregation]
```

## Agentic RAG

```mermaid
flowchart TD
 docs[Documents] --> chunk[Clean and chunk]
 chunk --> embed[Sentence transformers]
 embed --> chroma[ChromaDB]
 chroma --> retrieve[Authorized retrieval]
 retrieve --> verify[Hash and evidence verification]
 verify --> reason[Reason over evidence]
 reason --> enough{Sufficient evidence}
 enough -->|Yes| answer[Grounded answer]
 enough -->|No and below limit| rewrite[Rewrite query]
 rewrite --> retrieve
 enough -->|Limit reached| insufficient[Insufficient evidence]
```

## Data flow

```mermaid
flowchart TD
 csv[CSV or XLSX] --> validate[Validate and map actual columns]
 validate --> tables[Stores products snapshots sales]
 tables --> tools[Parameterized domain tools]
 tools --> result[AgentResult]
 result --> response[ChatResponse]
 result --> audit[Audit metadata]
```

## Branch ownership

```mermaid
flowchart TD
 main[Main baseline] --> context[Knowledge context]
 context --> approval{Human approves context commit}
 approval --> foundation[Foundation commit]
 foundation --> agents[Nine isolated agent branches]
 foundation --> rag[RAG branch]
 foundation --> security[Security branch]
 agents --> gate{Explicit integration approval}
 rag --> gate
 security --> gate
 gate --> candidate[Release candidate]
```

## Security and audit

```mermaid
flowchart TD
 principal[Authenticated principal] --> rbac[Authorization]
 rbac --> tools[Restricted tools]
 rbac --> retrieval[Scoped retrieval]
 retrieval --> hash[Verify document hash]
 hash --> evidence[Untrusted evidence boundary]
 tools --> audit[Redacted audit event]
 evidence --> audit
 audit --> chain[Hash chain]
```

## Test relationships

```mermaid
flowchart TD
 tests[Validation suite] --> foundation[API and schemas]
 tests --> domain[Domain and missing-data tests]
 tests --> rag[RAG relevance and iteration limits]
 tests --> security[RBAC and tamper tests]
 tests --> integration[Approved end-to-end tests]
```
