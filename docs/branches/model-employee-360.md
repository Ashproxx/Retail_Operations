# Employee 360 assistant

Owns app/employees/service.py and conversational tests. Scoped name resolution prefers normalized full names, partial tokens and conservative fuzzy candidate confirmation. Profiles use the security allowlist before response serialization; salary/benefit requests from unauthorized roles are denied. HR memory is namespaced separately from retail, reauthorized on every follow-up. Missing ratings remain explicit unknowns. Source-snapshot staffing aggregates and authorized payroll are descriptive only.

Tests cover ambiguity, selected-person attendance/salary, null ratings, manager redaction, analyst denial, changed store grants and field-only audit logs. No hiring/firing/promotion decision, HR policy invention or individual-sales attribution. No LLM is needed to retrieve structured records. Future HR policy RAG can use the retained authorized document service once actual policies are supplied.
