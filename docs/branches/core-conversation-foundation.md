# Conversational foundation

Purpose: typed turns/context, authorized discovery and additive analytical imports.
Owned: contracts.py, catalog.py, ingest.py and test_catalog.py.
Inputs: runtime Repository, server-owned RequestContext, explicit mapping and observed rows.
Exposed: Catalog.observations/discover/products/product360, import_observations, Turn and Context.
Data: additive retail_observations table; legacy domain_records read-only. Exact canonical identities take precedence in the analytical view, never deleting original records.
Tests: scoped location discovery, denied store, raw preservation, Product 360 unknowns, atomic failure, duplicate identities and CSV formula rejection.
Checklist: [x] contracts [x] discovery [x] raw import [x] Product 360 [ ] conversational API integration.
Limitations: absent legacy attributes remain null; legacy inventory-only views cannot invent sales or product names. Operator imports require explicit column mapping. No real dataset supplied.
Baseline: market-calendar d36f97a; branch dependencies are immutable parent history.
Knowledge delta: retail_observations + legacy Repository -> authorized Catalog -> discover/Product 360 -> conversation context.
