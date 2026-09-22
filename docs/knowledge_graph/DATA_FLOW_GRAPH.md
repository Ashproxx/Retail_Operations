# Planned data flow

```mermaid
flowchart TD
 csv[CSV or XLSX] --> validate[Validate and map actual columns]
 validate --> tables[Stores products snapshots sales]
 tables --> tools[Parameterized domain tools]
 tools --> result[AgentResult]
 result --> response[ChatResponse]
 result --> audit[Audit metadata]
```

No source data is present. Infer no actual table columns. Validate dates, numerical values, duplicates, missing values, stock and identifiers at ingestion. SQLite through SQLAlchemy is a proposed local starting point; Azure deployment remains future work. Never expose development fixtures as real data.
