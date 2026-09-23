# Test coverage map

| Suite | Behavior |
|---|---|
| tests/foundation | Schemas, SQL lifecycle, health, error hygiene; endpoint expectations updated for integration |
| tests/router and tests/<domain> | Original routing and eight domain suites, unchanged |
| tests/rag, tests/security | Original local retrieval, integrity and role suites, unchanged |
| tests/integration/test_api.py | All agent IDs, seven prompt queries, follow-up isolation/revocation, aggregation/conflicts, feedback, audit, errors |
| tests/integration/test_storage.py | CSV/XLSX atomic mapping, dates, formulas, duplicates, invalid stock, authorization before DB |
| tests/integration/test_rag.py | Real local Chroma and sentence-transformers fixture, rehashed tampering, manifest corruption, support/API integration |
| tests/integration/test_provider.py | Mocked Ollama wire protocol and unavailable/malformed responses |

Latest numerical results and outstanding runtime checks: [integration report](../integration/REPORT.md). Fixture tests do not establish pretrained semantic quality or production performance.
