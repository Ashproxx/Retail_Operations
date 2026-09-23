# M1 foundation delta

Approved base: 3cc1a8df36c49147daac2c3967f37020bb0f5654. Master/context graphs remain unchanged. Branch JSON provides file ownership, import and test relationships.

```mermaid
flowchart TD
    env[Environment] --> config[Settings]
    config --> app[FastAPI factory]
    app --> health[Database health]
    health --> db[SQLAlchemy lifecycle]
    app --> logs[Metadata logs]
    app --> errors[Sanitized errors]
    contracts[Pydantic contracts] --> agents[BaseAgent interface]
    contracts --> dataset[DatasetLoader interface]
    tests[Foundation tests] --> app
    tests --> db
    tests --> contracts
```

Implemented: validated configuration, API factory/lifespan, root/health, docs/OpenAPI, errors/logging, schemas, BaseAgent and data interfaces, transactional database lifecycle. Tests cover failures as well as normal inputs.

Only interfaces exist for DatasetLoader, RetailRepository and BaseAgent. No agent/RAG/business source integration. No production retail data. RequestContext is internal and must eventually come from trusted authentication; QueryRequest rejects role claims. AuditEvent is a schema only, with durable audit and integrity owned by later work.

New dependencies are justified in BRANCH_README.md. No cross-branch propagation or SHARED DELTA. Foundation publication must be verified before M1 earns 10%; M0 already earned 5%.
