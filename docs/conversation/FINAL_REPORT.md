# Conversational RetailOps review report

Date: 2026-09-30. Status: READY FOR HUMAN REVIEW. Verified engineering milestone completion: 100% (synthetic acceptance scope).

Integration branch: `integration/conversational-retailops`. Implementation commit: `c613603e503f675d9da2651d05e3af07438f54f1`.

## Delivered

The assistant is the primary conversational workspace at `/assistant`. It discovers authorized location/product choices from loaded data, clarifies one missing field at a time, retains context across follow-ups and resolves duplicate names through explicit selection. It exposes exact sales totals, inventory snapshots, Product 360, stock-aware diagnoses, category/store peer averages and advisory recommendations.

Inline charts support vertical/horizontal/grouped/stacked bars, line/multi-line/area, pie/doughnut, scatter and heatmap, with compatible choices, text interpretation and accessible tables. The original dashboard remains available.

Windows launch and verification now include IANA timezone data and CRLF-compatible browser token parsing. The branch source guard checks Git-normalized content. Earlier stale completion records have been reconciled against actual tests.

## Agents

| Capability | Verified behavior |
|---|---|
| Router | Progressive clarification, context, compound intents, bounded local-model fallback |
| Analytics | Decimal revenue, period/group comparisons, diagnostics and peer averages |
| Inventory | Observed snapshots, stockout/reorder evidence; original adapter preserved |
| Demand | Apparel profile, multiple models, chronological evaluation and explanations |
| Pricing | Read-only existing agent evidence and promotion-policy context |
| Supply chain | Scoped product choices and existing supplier comparison |
| Orders | Purchase choices and existing order/status analysis |
| Customer service | Existing scoped FAQ/policy agent and local RAG |
| Returns | Purchase/reason/receipt/unit clarification and existing eligibility/refund analysis |
| Competition | Internal similarity, price/performance comparison and explicit external-data limitation |

## RAG and forecasting

Local ingestion, chunking, embeddings, Chroma storage, bounded iterative retrieval, source metadata and integrity checks remain intact. Conversation policy evidence contributes document IDs to audit events. Exact numerical facts come from structured tools. Unconfigured retrieval is disclosed.

Apparel models include naive, seven-day moving average, exponential smoothing, weekly seasonal naive, weekday means and a yearly seasonal baseline when history permits. Shared chronological folds measure MAE/RMSE/WAPE; no future observations enter prediction. Zero-volume WAPE and missing history remain unknown. Calendar/season context is configured. Bands are heuristic, not calibrated confidence intervals.

## Validation and milestones

- Windows: 201 Python tests passed, none failed/skipped; dependency and source-preservation checks passed.
- Both real-browser gates passed, including desktop/mobile, chart choices, full follow-up flow, authentication and memory-only token handling. Captured desktop/mobile screens were inspected.
- The final Linux CI run is [36731448837](https://github.com/Ashproxx/Retail_Operations/actions/runs/36731448837); both jobs and every required validation step passed at the implementation commit above. M9 is verified.
- [Validation details](VALIDATION.md), [milestone ledger](../knowledge/MILESTONE_LEDGER.md), [deliverable checklist](../DELIVERABLE_CHECKLIST.md), [every branch and checkpoint SHA](../knowledge/BRANCH_REGISTRY.md).

## Limitations and review

No real retail dataset was supplied. Synthetic acceptance verifies implementation behavior, not actual business accuracy or source-column mapping. External competition is unconfigured. Natural-language parsing is bounded; recommendations, similarity scores, diagnostic thresholds and uncertainty bands carry stated assumptions. Single-worker operation and bounded local datasets remain the deployment scope. No business operation is executed by recommendations.

Main remains at `d39db70d0a8b429052340d691f01ca2769c1e8cc`; it was not modified or merged. Review the integration diff and [launch the demo](RUN.md). After explicit human approval, merge the reviewed candidate into main through the normal repository review process. Do not treat this report or a passing CI run as merge authorization.
