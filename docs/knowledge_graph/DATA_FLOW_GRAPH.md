# Data flow

See the implemented system, multi-agent, RAG and security flows in [ARCHITECTURE.md](../../ARCHITECTURE.md).

CSV/XLSX -> explicit mapping -> domain validation -> transactional SQL -> authorized records -> domain result -> conflict/aggregation -> audit -> response.
