# Test coverage

Baseline test coverage: no tests or application code. No coverage percentage claimed.

| Planned owner | Required cases |
|---|---|
| foundation | Health, schemas, invalid payloads, agent failures, loader validation |
| router | Inventory/pricing/multi-intent, unknown, low confidence |
| each domain agent | Deterministic rules, absent data, invalid inputs, result schema, demo |
| RAG | Ingest/retrieve relevance, iteration bound, tamper rejection, insufficient evidence |
| security | Unauthorized tools/retrieval, hashes, audit chain, safe logging |
| integration | Single and multi-agent requests, conflict handling, startup, follow-ups with RBAC |

M0 validation: parse graph JSON, unique IDs, valid edge endpoints, weights total 100, required documents present, correct branch/base, diff scope and whitespace checks. Application tests are not applicable yet.
