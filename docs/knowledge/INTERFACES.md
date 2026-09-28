# Conversational interfaces (planned contracts)

POST /api/conversation: authenticated message or structured action, session_id, no client authority fields. Response: status, summary, context, one clarification with database options, key numbers, findings, recommendations, compatible charts, provenance and actions.

GET /api/conversation/options: dimension discovery filtered to current principal permissions. Context state is namespaced from legacy orchestration memory; records are reauthorized every turn.

Catalog -> canonical observations + raw metadata; taxonomy -> explicit normalized labels; analytics -> decimal-safe facts; diagnostics -> fact/analysis/recommendation separation; forecast -> chronological folds and model metrics; competition -> documented heuristic score; charts -> typed labels/datasets, never arbitrary script.

Keep existing /api/chat, /api/query, /api/rag and feedback contracts intact. RAG facts are cited; structured numerical facts come only from SQL.
