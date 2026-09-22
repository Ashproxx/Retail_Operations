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

Remote main and context/project-knowledge exist. Context starts at c21658e55c96d7adc78b82d2e2f3d2b17d226144; M0 publication commit is 526b5bbe82e9ca06a64389e37d5cacb9b4a0eca7. All later branches remain planned.
