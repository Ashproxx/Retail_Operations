# M19 model review dashboard - isolated candidate

Branch ui/ml-dashboard from c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. Scope: app/ml_dashboard, tests/ml_dashboard, scripts/export_ml_dashboard.py, docs/ml-dashboard and these records. Existing website and protected branches are untouched.

Candidate `/ml` shows frozen selected-before-test curves, 80% interval limits, measured 80%/95% coverage, metrics, comparison tables, exclusions and auxiliary status. Coffee/bronze styling, responsive layout, reduced-motion support and accessible table alternatives. Tokens remain in memory only. APIs authenticate and audit reads; managers/analysts see authorized stores only; global aggregate leaderboard and auxiliary evidence are ADMIN-only; HR roles denied. No client-supplied scope is trusted.

Reports are exported as local data from pinned commits: M17 6b86795 and M18 70b0241. Source code is not merged. Checksums detect accidental report changes; this is not a signature against a malicious local administrator. Missing evidence fails closed. Independent launcher port 8002; normal server remains unchanged. Live feed honestly reports unavailable until M20 integration approval.

Remaining M19 scope: actual live freshness/stream wiring, missing-data/feature-importance views and real benchmark comparisons cannot be demonstrated by the current evidence. M20 still needs exact-commit approval. No training, promotion or external transmission occurs in the dashboard.


## Run locally

Fetch origin so the pinned report commits exist, then:

```powershell
.venv/Scripts/python.exe -m scripts.export_ml_dashboard
.venv/Scripts/python.exe -m app.ml_dashboard.launch
```

Open http://127.0.0.1:8002/ml and paste the temporary terminal token. Use `--role STORE_MANAGER --stores ST01` for a scoped review. The local imported workbook database is required; no source workbook or database is stored in Git. The `/ml` page shell is public and contains no business results before authentication.

Evidence dependencies are data-only exports from the isolated M17 and M18 branches, not integrated application code. Frozen comparisons remain research evidence; the dashboard never promotes a candidate or changes baseline fallback.
