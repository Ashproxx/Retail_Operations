# Branch README

Branch: context/project-knowledge
Parent branch / base commit: main / c21658e55c96d7adc78b82d2e2f3d2b17d226144
Milestone: M0 — BLOCKED; official completion 0%
Owner scope: knowledge graph, governance and branch metadata
Human approval status: context work authorized; foundation context commit approval pending

## Purpose
Establish an auditable implementation plan before application development.
## Source-defined responsibilities
Preserve all nine PDF agent roles and FastAPI, LangGraph, ChromaDB, sentence-transformers and Ollama direction. Azure is a later deployment target.
## Allowed file scope
docs/knowledge_graph/*, docs/governance/*, BRANCH_README.md, BRANCH_DELIVERABLES.md.
## Interfaces consumed
PDF design specification; baseline README defines no runtime interfaces.
## Interfaces produced
Planned contracts in INTERFACE_REGISTRY.md; no executable interface.
## Deliverables
Master graph with seven views and JSON, ownership/interface/data/test/branch maps, baseline audit and governance.
## Tests
Documentation validation performed locally; no application tests exist.
## Knowledge graph changes
Planned application, agent, branch, milestone, data and security nodes; existing documentation nodes.
## Data dependencies
No dataset, orders, supplier records or policy documents supplied. Production grounding cannot be claimed.
## Known limitations
GitHub branch creation returned HTTP 403 Resource not accessible by integration. No remote milestone delivery. No application implementation.
## Cross-branch dependencies
Foundation requires human approval of a published context commit; isolated agent/platform/security work requires pinned foundation. No SHARED DELTA.
## Security considerations
No credentials or private data included. Retrieved content will be treated as untrusted, with authorization before access and hash checks before reasoning.
## Last validated commit
Baseline c21658e55c96d7adc78b82d2e2f3d2b17d226144; local M0 validation applies to the commit containing this file. Use git rev-parse HEAD for its identifier.
## Latest test result
PASS: graph JSON, unique node IDs, edge endpoints, 16 documents, seven views, weights 100%, branch/base and allowed paths. Remote verification remains blocked.
## Next tasks
Restore repository connector write access; publish and verify M0; approve exact M0 commit; create foundation branch and implement M1.
