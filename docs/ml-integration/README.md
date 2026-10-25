# Integrated research candidate

The user approved the exact source assembly on October 25, 2026, and authorized future development-branch work without routine confirmation. Main still requires approval. This branch is `integration/ml-realtime-candidate`; it descends from the approved showcase base and contains all six commits in SOURCES.json. Main and the original showcase branch were not modified.

## Run on another laptop

Fetch and check out `integration/ml-realtime-candidate`. Follow the existing project setup/import instructions to create a virtual environment and import the source workbooks locally; private workbooks and the SQLite database are not added to Git. Install `requirements.txt`; model experiments additionally use `requirements-ml.txt` and `requirements-auxiliary.txt` if present. Run from the repository root:

```powershell
.venv/Scripts/python.exe scripts/export_ml_dashboard.py
.venv/Scripts/python.exe -m app.ml_dashboard.launch --port 8002
```

Open http://127.0.0.1:8002/ml and enter the temporary token printed in that terminal. The token lasts eight hours and is not saved in browser storage. Disconnect clears results and cancels live requests. The launcher also serves the existing retail, employee and dataset pages. It binds only to this laptop. An imported database at another location can be supplied with `--database PATH`.

For a scoped demonstration add `--role STORE_MANAGER --stores ST01` (or ANALYST with the required store IDs). HR roles cannot read model or live retail results.

The default live feed is off. To demonstrate arrivals, first copy the imported database to a separate demonstration database while its server is stopped, then add `--database PATH_TO_COPY --stream-mode simulator`. Simulator events remain explicitly synthetic in a separate table; they do not update imported sales, stock or research scores. The dashboard polls bounded SSE batches of at most 100 events every five seconds, retains 20 rows, and resumes from the last received ID after network interruption. An initial connection replays stored events from ID zero, so a large backlog takes time to drain. Upgrade to a scoped snapshot cursor before using this for high-volume monitoring.

Add `--weather` to enable approved public Open-Meteo requests for Navi Mumbai coordinates. Retail and employee records are never sent. Weather is context only, not a validated forecasting feature. Without access, freshness and unavailable/stale readings remain visible. Existing webhook mode requires a locally configured `RETAILOPS_STREAM_HMAC_KEY` of at least 32 characters, signed events and an authorized bearer token; no secret belongs in Git.

## Interpretation and remaining work

Frozen benchmark exports keep their original commit pins and checksums. Live event counts are independent of those benchmarks. Missing events are unknown coverage, never assumed zero sales. No ML candidate is promoted: the original application baseline behavior remains intact. Registry, model and evaluation code is available for research, not automatically substituted into business decisions.

M17/M18 acceptance still needs independent real-world evidence, historical forecast vintages, genuine inventory/lead-time observations and human-reviewed labels. Existing final-test labels must not be reused for tuning and called an independent evaluation. Forecast undercoverage and failed delivery comparisons remain disclosed. Supplemental pooled and similarity reports are available in the repository but are not added to the frozen dashboard leaderboard. No production release or main merge is included.

Source branch records and knowledge graph deltas are archived under `sources/`; the current source manifest supersedes older proposed integration tables. See VALIDATION.md for checks and remaining browser limitations.
