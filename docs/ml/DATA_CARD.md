# Data card: RetailOps AIML extension

Audited 2026-10-23 against code base `c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93`. Source label: **synthetic-workbook**. Counts below are measured from the local imported SQLite database, not live retail systems. Reproducible SQL and import hashes are in [DATA_AUDIT.json](DATA_AUDIT.json). Original workbook column/missingness evidence remains in [the Phase 3 audit](../phase3/DATA_AUDIT.json).

## Sources and permitted uses

| Source | Verified contents | Intended use |
|---|---|---|
| Synthetic Navi Mumbai sales workbook | 75,000 transaction lines; 59,088 orders; 20 stores; 85 SKUs; six categories | Observed-sales forecasting and sales/delivery analysis |
| Competitor sheet | 24,804 weekly estimated records | Historical competitor context, not live market truth |
| Employee workbook | Import receipt: 150 employees and 20 staffing records | Existing HR workspace; excluded from sales ML features |
| Weather | Not connected or downloaded in M14 | Future approved external signal |
| Real retail benchmark | Not selected or downloaded | Future independent real-data evaluation after licence approval |
| POS simulation | Not implemented | Future synthetic-stream testing; not real sales |

Sales workbook SHA-256: `88da0500b3f3c27bba210a1608f524a3ccdf2365570b9d2c115ca9a06d686c01`.
Employee workbook SHA-256: `474322a5116171fc73b6418499e1302b44824cbbd07793712243432be53c174b`.
These hashes are stored import receipts, not a new hash of downloaded files. Public redistribution rights have not been established. Source workbooks, database, personal records and keys stay outside Git; committed audit evidence contains aggregates only.

## Observation grain, labels and coverage

`sales_transactions` stores one immutable transaction line identified by txn_id. Daily targets sum quantity after selecting the authorized scope. Monetary values are integer paise; source net amounts reflect whole-rupee rounding. Category is normalized by the importer while raw columns remain in payload. Competitor records are weekly and cannot be assigned a reliable within-week publication time.

Dates: 2025-09-29 through 2026-09-29, **366 inclusive observed calendar dates**, not 365. Total quantity is 87,784 units and recorded net revenue is 9,719,600,700 paise. Line quantities range 1–3; no zero/negative lines exist. This does not establish the absence of zero-sales days.

| Aggregation | Series | Observed dates per series | Consequence |
|---|---:|---:|---|
| Chain | 1 | 366 | Contiguous recorded totals; constituent completeness still uncertain |
| Store | 20 | 348–366 | Some stores have missing dates |
| Store/category | 120 | 73–354 | No series has the full 366 dates; check each fold |
| Store/SKU | 1,700 | 1–152 | Extremely sparse observations; true zeros unknown |

Missing target dates must remain unknown. Do not use the potential 1,700 × 366 grid as if it were fully observed. Report the number of eligible windows for each horizon; missing windows are exclusions, not zero-error predictions. Positive-only ingestion limits use of intermittent-demand methods until explicit exposure/zero labels are supplied.

## Missingness, outliers and quality risks

Original source audit records 3,576 missing actual_delivery_date values and 2,933 missing delay_days_vs_promise values. These may represent unresolved deliveries and must not become on-time labels. Group lines by order/store before evaluating delivery models. No on-hand stock, returns table, supplier lead-time table or verified promotion schedule exists.

DATA_AUDIT.json records chain daily minima, maxima and mean for data understanding only. No outlier was deleted and no distribution cutoff was fitted on the test period. M15 should fit robust diagnostics on training observations, flag rather than silently remove plausible sales peaks, and log the policy. Duplicate txn_id is prevented by the primary key/import validation; source audit reports zero duplicate transactions. No new row-level missingness study is claimed beyond the existing audit.

Synthetic transactions and competitor estimates are not independent real-world evidence. Stable product metadata can drift without an effective-date history. Source dates include the future relative to older experiments, so all consumers must respect the experiment cutoff rather than simply reading the latest row.

## Leakage and privacy

Exclude employee identity, salary and personal fields from ML extracts. Exclude delivery outcomes when predicting delay. Do not use realized future prices, discounts, channel mix, sales, current-month totals, weekly competitor sales or observed future weather as predictors. Preserve role/store filtering before serving outputs; a global model must not expose out-of-scope series through explanations or charts.

Every result must distinguish synthetic-workbook, live-weather-joined, real-benchmark, or synthetic-stream. Joining real weather to synthetic sales does not turn the sales into real observations. Real historical datasets remain offline benchmarks, not live POS feeds.

## Reproduce the metadata audit

Run from the repository with the existing local database. This checks only aggregate metadata; it does not train a model or score the held-out test block:

```python
import json, sqlite3
from pathlib import Path
report = json.loads(Path('docs/ml/DATA_AUDIT.json').read_text())
connection = sqlite3.connect('file:.retailops/phase3/retailops.db?mode=ro', uri=True)
connection.row_factory = sqlite3.Row
try:
    for name, entry in report['queries'].items():
        actual = [dict(row) for row in connection.execute(entry['sql'])]
        assert actual == entry['rows'], name
finally:
    connection.close()
```

The local database is required for this check and is not part of Git. A different source snapshot should produce a new versioned audit rather than overwriting recorded findings without explanation.
