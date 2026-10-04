# Phase 3 local workspace

Run from the repository with Python 3.12 and the existing requirements installed. No new service or cloud account is required. The source workbooks are explicitly synthetic POC data and are intentionally absent from Git. Import your supplied files once:

```powershell
New-Item -ItemType Directory -Force .retailops/phase3
.venv/Scripts/python.exe -m scripts.import_sales_data --file C:/Users/User/Downloads/RetailOps_NaviMumbai_Sales_Dataset.xlsx --database sqlite:///.retailops/phase3/retailops.db
.venv/Scripts/python.exe -m scripts.import_employee_data --file C:/Users/User/Downloads/RetailOps_NaviMumbai_Employee_Dataset.xlsx --database sqlite:///.retailops/phase3/retailops.db
.venv/Scripts/python.exe -m app.enterprise.launch
```

Create `.retailops/phase3` before a first import if it does not exist. Open `http://127.0.0.1:8000/models`, choose an active workspace, press Connect and paste the temporary token printed by the launcher. It expires after eight hours and is retained only in browser memory; reloading needs reconnection. Navigation within the website keeps the connection but starts a separate conversation. `--port` selects another local port. The local launcher defaults to ADMIN for this POC; it binds only to loopback.

For access testing, use `--role STORE_MANAGER --stores ST01` or `--role ANALYST --stores ST01`. Store IDs are administrative grant configuration, never required from ordinary users. HR_ADMIN has global HR access, HR_USER has assigned-store HR access, STORE_MANAGER gets safe assigned-store profiles, ANALYST gets aggregates only. HR-only roles have no retail permission. Use separate launch instances when comparing roles; production identity provisioning is outside this local POC.

## Data and behavior

- `/models` is the public selector. `/retail` and `/employees` query authenticated SQL data. `/employee-work` and `/management` are informational Coming Soon pages.
- The browser root serves the selector; API clients requesting JSON retain the existing root response. `/assistant`, `/dashboard` and the original APIs remain available for prior-phase compatibility; their explicit showcases are not the Phase 3 source.
- Source metadata and SHA-256 import receipts prevent repeated identical imports. Invalid new imports roll back facts. Changed workbooks containing existing transaction/employee IDs are not silently overwritten: validate a fresh database and deliberately replace the local snapshot after review.
- Net sales use recorded discounted source amounts, including whole-rupee source rounding. Delivery metrics count distinct orders. Competitor facts are synthetic weekly estimates, not live results. No on-hand inventory data exists. Forecasts are selected historical baselines, not proven future demand accuracy.
- Employee data is a source snapshot. Missing values stay unknown. Store-level sales cannot be attributed to individual employees. Policies are not invented; the existing signed RAG pipeline is retained for future supplied, authorized policy documents.
- Local runtime is one process/worker. Use the existing authenticated runtime configuration for deployments; multi-worker session locking, identity administration, external audit anchors and production load qualification need separate work.

## Verification

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/check_branch_scope.py
.venv/Scripts/python.exe -m scripts.validate_phase3_sources --sales C:/Users/User/Downloads/RetailOps_NaviMumbai_Sales_Dataset.xlsx --employees C:/Users/User/Downloads/RetailOps_NaviMumbai_Employee_Dataset.xlsx --database .retailops/phase3/retailops.db --output validation-output/phase3/source-reconciliation.json
```

`node scripts/check_phase3.cjs` runs browser acceptance with disposable, labelled CI fixtures. Set `RETAILOPS_PHASE3_DATABASE` to the imported database and `RETAILOPS_PYTHON` to the Python executable for full supplied-workbook browser acceptance. Playwright must be available through Node's module resolution. Reports and screenshots are written under ignored `validation-output/phase3`; no employee rows or credentials are uploaded by this check.
