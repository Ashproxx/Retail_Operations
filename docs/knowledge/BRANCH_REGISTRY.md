# Branch registry

main is read-only. integration/release-candidate remains the runnable prior release.
baseline/conversational-intelligence is pinned at b74a06df9753e7e20f66c4c6bb8874114fe50a9f.

| Branch | Owned work |
|---|---|
| context/project-knowledge | Audit, graph, milestone ledger and decisions |
| core/conversation-foundation | Context, catalog, discovery, import and API contracts |
| feature/product-taxonomy | Configurable taxonomy and Product 360 normalization |
| feature/market-calendar | Configurable market context and natural-language dates |
| agent/router-conversation | Intent detection, clarification and follow-ups |
| agent/analytics | Analytics, low-sales diagnostics and evidence-led recommendations |
| agent/demand-forecasting-conversation | Apparel forecast profiles and chronological model selection |
| agent/competition-intelligence | Explainable internal substitute comparisons |
| feature/charting | Compatible chart specifications and interpretation |
| feature/conversational-ui | Conversation-first interface and inline visualizations |
| integration/conversational-retailops | Approved feature composition, wiring and end-to-end QA |

Existing inventory, pricing, supply, orders, support and returns implementations will be reused unchanged unless a concrete adapter change is necessary. Their source branch heads will not be overwritten with integrated history. Existing demand source history will be preserved; new conversational forecast work will be added only to its designated branch. Features share typed interfaces and are integrated only into the dedicated candidate.

The conversational forecast branch uses a suffix to preserve the original `agent/demand-forecasting` source head. Integrated corrective changes and acceptance tests live on the integration branch; feature branch checkpoints remain intact.
