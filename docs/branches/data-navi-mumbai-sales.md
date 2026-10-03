# Navi Mumbai sales foundation

Owns app/enterprise/data.py, imports.py, sales import command and import tests. Indexed transactions, products, competitor estimates, store metadata and hash-based import receipts retain raw columns. Net revenue stored as integer paise from source net_amount_inr; source rounds to whole rupees (INR 0.50 reconciliation tolerance). Taxonomy adds Ethnic without replacing raw categories.

Verified actual workbook: 75,000 transactions, 59,088 orders, 85 SKUs, 24,804 competitor rows, 20 stores; 2025-09-29 through 2026-09-29; INR 97,196,007 net revenue. Atomic invalid-row rejection/idempotence/type and taxonomy checks: 4 passed. No inventory is inferred. Source files and runtime DB stay ignored/local. Integration target: integration/dual-model-retailops.
