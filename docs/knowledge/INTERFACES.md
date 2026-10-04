# Conversational interfaces (implemented contracts)

POST /api/conversation: authenticated message or structured action, session_id, no client authority fields. Response: status, summary, context, one clarification with database options, key numbers, findings, recommendations, compatible charts, provenance and actions.

GET /api/conversation/options: dimension discovery filtered to current principal permissions. Context state is namespaced from legacy orchestration memory; records are reauthorized every turn.

Catalog -> canonical observations + raw metadata; taxonomy -> explicit normalized labels; analytics -> decimal-safe facts; diagnostics -> fact/analysis/recommendation separation; forecast -> chronological folds and model metrics; competition -> documented heuristic score; charts -> typed labels/datasets, never arbitrary script.

Keep existing /api/chat, /api/query, /api/rag and feedback contracts intact. RAG facts are cited; structured numerical facts come only from SQL.

## Phase 3

Phase 3 plan: /models (root selector), /retail, /employees; authenticated /api/retail/options + /chat and /api/employees/options + /search + /chat + /overview. Server-owned roles/scope, separate memory namespaces; structured cards, compatible chart specs, evidence and no automatic business writes.

Implemented: public GET /models, /retail, /employees, /employee-work, /management; GET / serves HTML for browser Accept and retains JSON otherwise. WorkspaceTurn requires session_id; optional message/action/value only. GET /api/employees/search accepts q; every data endpoint uses bearer authentication. HR_ADMIN and HR_USER add HR-only grants; existing roles keep existing retail permissions. Model namespaces phase3:retail and phase3:employees isolate state even with the same client session ID.
