# Model selector and dual workspace website

Branch: feature/model-selector-dashboard. Parent Employee 360 checkpoint: df44da7. Owns app/enterprise/static, authenticated routes, local launcher, app/main.py mounts, tests/phase3/test_workspace_api.py, disposable CI browser server and scripts/check_phase3.cjs. Uses the already imported sales and employee tables; creates no business rows at normal startup. Source-validation script reconciles local supplied workbooks without committing their records.

Public routes: /models, /retail, /employees, /employee-work, /management. Authenticated APIs: GET /api/retail/options, POST /api/retail/chat, GET /api/employees/options, GET /api/employees/search, GET /api/employees/overview, POST /api/employees/chat. Shared WorkspaceTurn accepts no client-controlled role/store grants.

Deliverables: four cards, two active assistants, source badges, responsive employee profile/search/staffing, retail charts and accessible tables, separate session identifiers, in-memory connection token and explicit future pages. Reuses installed ECharts. Fresh-app table registration is tested. Source imports and original agent implementations are inherited, not edited here.

Validation: eight Phase 3 Python tests passed; full supplied-workbook browser flows passed on 2026-10-04. Latest verified parent remains df44da7 until this checkpoint is committed; final immutable checkpoint and complete gate evidence are recorded in integration documentation. Limitations and startup commands: docs/phase3/RUNBOOK.md. Main merge requires final human authorization.
