# Hard milestones

Official completion: **5%**. M0 PASS: documentation validated and published; all others NOT STARTED. Only fully passed milestones earn credit.

| Milestone | Weight | Branch | Exit criteria |
|---|---:|---|---|
| M0 | 5% | context/project-knowledge | Audit, baseline, seven master graph views, JSON graph, ownership, interfaces, branch graph, governance, commit and verified push |
| M1 | 10% | foundation/core-platform | Python package, config/env, logging, exceptions, Pydantic schemas, BaseAgent, database and dataset-loader interfaces, FastAPI health, tests, env example and gitignore |
| M2 | 8% | agent/router | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M3 | 9% | agent/inventory | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M4 | 7% | agent/order-fulfillment | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M5 | 8% | agent/supply-chain | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M6 | 8% | agent/pricing-promotions | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M7 | 6% | agent/customer-service | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M8 | 6% | agent/returns-refunds | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M9 | 8% | agent/demand-forecasting | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M10 | 7% | agent/analytics-reporting | Agent logic, typed inputs/outputs, deterministic tools, missing-data handling, unit tests, realistic demo, audit metadata, interfaces, branch docs and graph |
| M11 | 8% | platform/agentic-rag | Ingestion, cleaning/chunking, metadata, sentence-transformers, ChromaDB, top-k, relevance, bounded iterative reasoning/verification, evidence, hash hook and tests |
| M12 | 5% | security/privacy-integrity | Roles/RBAC before tools and retrieval, secret-safe config, document hashes, audit schema/chain and security tests |
| M13 | 5% | integration/release-candidate | Explicit approved commits/base, integration only of those changes, full tests, startup, end-to-end demos, docs, no secrets, main untouched |

Universal definition of done applies to every row. Order: M0, M1, M11, M2, M3, M9, M10, M6, M5, M4, M7, M8, M12, then approved M13. Never advance past failing mandatory criteria without a human-approved exception.


## Approved integration-session update

M0-M12 PASS: 95% weighted total, with exact source commits in `docs/integration/APPROVED_SOURCES.json`. M13 INCOMPLETE: local integrated code/tests/startup delivered, external model/data/container/CI validation remains as recorded in `docs/integration/REPORT.md`. Source-branch milestone records are preserved in `docs/integration/sources`. No main merge authorized.
