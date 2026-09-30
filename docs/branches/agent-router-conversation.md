# Conversational router and orchestration

Owned: app/conversation/service.py and test_service.py.
Interfaces: ConversationService.run(Turn, trusted RequestContext). Persisted context is principal/session scoped with the existing 24-hour TTL, namespaced from legacy memory and reauthorized on every turn.
Flow: intent -> dynamic discovery -> one clarification -> date/location/product context -> deterministic agents -> compatible chart -> evidence and actions -> receipt + audit.
Optional local model fallback may choose only an allowlisted intent with high confidence; it cannot supply facts, authority, IDs or tool arguments. Unknown language falls back to clarification.
Tests: today's sales/location resolution, date follow-up, chart chips, stock-constrained shorts, pronoun recommendations, internal competition, principal/session isolation and authorized options.
Checklist: [x] core scenarios in service [x] scoped memory [x] progressive clarification [x] HTTP/browser verification.
Limitations: operational order/refund/pricing workflows still defer to the existing authorized API when extra business parameters are required; they are not claimed complete in the new UX. No real dataset supplied.
Knowledge delta: Turn -> intent/entity/period -> pending slot -> Catalog -> analytical tools -> RAG context -> response/actions -> namespaced state/audit.

Integrated verification (2026-09-30): local Python suite and both real-browser gates passed. See `docs/conversation/VALIDATION.md` for tested scope and commit evidence. Feature checkpoints remain unchanged; this annotation belongs to the integration candidate.

Remote feature/checkpoint SHA: `68511819585296c47b6002c4f1f875808d221f7b`. Integration verification target: `c613603e503f675d9da2651d05e3af07438f54f1`; final CI evidence is recorded in `docs/conversation/VALIDATION.md`.
