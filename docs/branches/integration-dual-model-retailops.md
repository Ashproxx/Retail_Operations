# Dual-model integration candidate

Branch: integration/dual-model-retailops, based on website checkpoint faeae6e and Phase 2 f81bce0. Main remains d39db70d0a8b429052340d691f01ca2769c1e8cc. Original source branches and archived implementations are unchanged.

Purpose: compose the supplied synthetic sales/HR imports, separate scoped SQL assistants, four-model website, retained legacy agents/RAG and shared security into one local runtime. Owned integration deltas: branch guard, CI, validation/documentation/knowledge graph, and regression fixes for multi-token name resolution, individual-sales attribution and numeric workbook cells. Feature checkpoint branches remain immutable.

Contracts and tables: docs/knowledge/INTERFACES.md and DATA_DICTIONARY.md. Deliverables, exact checkpoints, current checks and limitations: docs/phase3/VALIDATION.md. The latest verified pre-integration checkpoint is faeae6e; final verified commit/CI are recorded in the report after completion. New tests include malformed name matching and numeric HR fields; existing 201-test baseline is retained. No paid deployment or main merge is performed.
