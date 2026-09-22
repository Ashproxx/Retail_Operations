# Branch lineage

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

Only main is confirmed remotely. Local context branch starts at c21658e55c96d7adc78b82d2e2f3d2b17d226144. No remote development branch was created because the connector denied the write. All later branches remain planned.
