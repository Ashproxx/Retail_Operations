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

## Remote checkpoint SHAs (2026-09-30)

These are the implementation checkpoint heads. A subsequent integration documentation-only commit may record completed CI without changing runtime code.

| Branch | SHA |
|---|---|
| agent/analytics | `b48be07849b00c0046826dd19bb14f8634fc1ab6` |
| agent/analytics-reporting | `26f58b0600e6df6c8a37523ebff2065f6705d73b` |
| agent/competition-intelligence | `b65e8be0ab09ed8bb20cd52fb2087a55782bee7c` |
| agent/customer-service | `5ecdbf6eab71715657b1a17e1305ab6702b8704d` |
| agent/demand-forecasting | `7a65d8dab39697ef62be14e5feda945efda55ac9` |
| agent/demand-forecasting-conversation | `c4b0d7e77f7eb10c42f35fe7c4cad40c4e2b156f` |
| agent/inventory | `bc1a4d5c1a3c62e81512b0b9cdbc6eceaa58d3ba` |
| agent/order-fulfillment | `21acc0898ce8b3f0f130bb21b8b4b2fbafc7851b` |
| agent/pricing-promotions | `57ff09d09ad74eb623d28168b63774df25ea3294` |
| agent/returns-refunds | `4a0b17d7d071e9cb203ccf3f5b6474e5d5eb61bb` |
| agent/router | `034946159557d9e88e2cd591b284f370fa6a9831` |
| agent/router-conversation | `68511819585296c47b6002c4f1f875808d221f7b` |
| agent/supply-chain | `bce3f17d4798e121a4c8f3aa1e697b093ab47e0d` |
| baseline/conversational-intelligence | `b74a06df9753e7e20f66c4c6bb8874114fe50a9f` |
| context/project-knowledge | `d4972ba9b51a87a64fcb3bb21432fea475ec79a9` |
| core/conversation-foundation | `d885093282c6532c135d33d9c4e020f9feb236b5` |
| feature/charting | `3aa2812c9a6ae4375462128edd0bbd1c4cfebec7` |
| feature/conversational-ui | `b1d0a7ad32877a65b17ec82899a794b9cd456c12` |
| feature/market-calendar | `d36f97a4a4a03d77815e7c1aa8e558d80359918c` |
| feature/product-taxonomy | `1b8b3602a38b7e7befaf865fdd731b989b177f05` |
| foundation/core-platform | `77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045` |
| integration/conversational-retailops | `c613603e503f675d9da2651d05e3af07438f54f1` |
| integration/release-candidate | `b74a06df9753e7e20f66c4c6bb8874114fe50a9f` |
| main | `d39db70d0a8b429052340d691f01ca2769c1e8cc` |
| platform/agentic-rag | `e3638225a5ea88ab6036ce6148f66d9208cedf5c` |
| security/privacy-integrity | `e55f640b416d2109bac8fbf9dea2622dbdc78577` |

## Phase 3

Phase 3 dependency sequence from f81bce0: codex/phase3-knowledge -> data/navi-mumbai-sales -> data/navi-mumbai-employees -> core/hr-access-control -> model/retail-operations -> model/employee-360 -> feature/model-selector-dashboard -> integration/dual-model-retailops. Each branch owns its named scope; later branches compose earlier checkpoints. Existing branch heads are preserved. UI branch owns both workspaces and selector to keep shared rendering consistent.

Published Phase 3 checkpoints: ac11d80 (knowledge), 177417f (sales), 216cdd1 (employees), ee72eb4 (HR security), dd34fc0 (retail), df44da7 (Employee 360), faeae6e (website). Final integration owns validation-only composition corrections and CI. See docs/phase3/VALIDATION.md for immutable final verification evidence.
