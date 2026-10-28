# Persistent seasonal demo

This is an opt-in local demonstration. Every generated sale, inventory movement and employee is simulated. Copied sales retain `copied-unverified` provenance; they are not verified real observations. Never use these records to claim real-world model accuracy or make employment decisions.

Run commands from the repository root with the existing virtual environment. The original database is opened read-only and copied through SQLite's backup API into memory; only catalog, stores and sales are imported. Credentials, sessions and staff are not copied. Use a new destination path. The source database and the ordinary launcher are unchanged.

## Initialize and build history

```powershell
.venv/Scripts/python.exe -m app.live_demo init --database .retailops/live-seasonal/retailops.db --source .retailops/phase3/retailops.db --months 24
.venv/Scripts/python.exe -m app.live_demo backfill --database .retailops/live-seasonal/retailops.db --max-slots 100
.venv/Scripts/python.exe -m app.live_demo status --database .retailops/live-seasonal/retailops.db
```

Omit `--months 24` for the seven-day quick start. Omit `--source` to use one explicitly fictional store and product. Backfill defaults to completed days through yesterday in Asia/Kolkata; `--intraday` permits only elapsed hourly slots today. `--through YYYY-MM-DD` bounds a historical run. No events are generated within the imported sales date range. Gaps there remain unknown rather than invented zero sales. Each atomic slot saves its checkpoint with sales and inventory; restarting resumes from the saved slot. Concurrent workers serialize writes and cannot duplicate a checkpoint.

## Keep the demonstration running

Run the web server and worker in separate terminals after initialization/backfill:

```powershell
.venv/Scripts/python.exe -m app.live_demo launch --database .retailops/live-seasonal/retailops.db --port 8003
.venv/Scripts/python.exe -m app.live_demo worker --database .retailops/live-seasonal/retailops.db --intraday --interval 30 --max-slots 100
```

Open `http://127.0.0.1:8003/models` and enter the eight-hour token printed in the server terminal. Keep the token private. Scoped roles require, for example, `--role STORE_MANAGER --stores DEMO1`; HR roles expose staff only according to existing role permissions. This launcher is localhost-only, does not send email and does not change the normal authentication setup.

Daily operations is added to the existing retail, models, datasets and employee pages. It shows source labels, freshness, filters, daily/monthly totals and inventory from signed movements. Today is compared with yesterday through the same local time. Missing opening balances stay unknown. Only the generated store/product subset has simulated stock; copied sales do not establish historical inventory. HR views distinguish planned shifts from recorded attendance. Exports contain the displayed authorized page; use the API cursor to request subsequent pages. The ledger's arrival cutoff supports historical knowledge snapshots.

The worker wakes every 30 seconds but generates hourly slots, not continuous real sales. Stopping it retains history. The website marks a stopped/stale worker. Local generation cannot continue while the laptop is off. A production host would need a persistent disk and a separately supervised worker; no hosting has been deployed.

## Configuration and seasonal assumptions

`app/live_demo/seasonal.json` is the sample configuration. Copy it to a new local JSON file and pass `--config <file>` during initialization. Its validated configuration, seed, scenario and version are saved in the database. Editing the JSON afterward does not change an existing scenario; initialize a separate database for different assumptions. Do not overwrite an existing scenario to retune history.

Monthly weights use actual catalog categories; unconfigured categories have a neutral factor. Weekday, explicitly dated calendar events, promotion and bounded trend factors combine under a cap. Demand uses seeded dispersion and is limited by stock; unavailable demand is recorded separately, not as fulfilled sales. Replenishments arrive after a configured lead time. Returns reference original sales, and damaged returns do not replenish available stock. Staff identities and weekly rest days are synthetic.

No festival dates are claimed as verified. The supplied calendar is empty and the UI warns about missing years. Optional event entries need explicit start/end dates, category factors, region and provenance (for example `manually supplied demo assumption`); they are never automatically repeated in future years. These factors are simulation assumptions, not estimated causal effects.

## Imports, corrections and recovery

```powershell
.venv/Scripts/python.exe -m app.live_demo import --database .retailops/live-seasonal/retailops.db --file local-events.json
.venv/Scripts/python.exe -m app.live_demo correct --database .retailops/live-seasonal/retailops.db --event EVENT_ID --reason 'Operator correction' --actor local-operator --replacement-units 2
.venv/Scripts/python.exe -m app.live_demo backup --database .retailops/live-seasonal/retailops.db --output .retailops/backups/seasonal-new.db
```

JSON imports are limited to 5 MB and 5,000 event objects. Each needs a stable `identity`, `store`, `sku`, `kind`, integer `quantity`, aware ISO `at`, and appropriate integer money/stock fields. Money is paise, discount basis points. Example opening record for the no-source quick start:

```json
[{"identity":"opening-demo-1","store":"DEMO1","sku":"DEMO-SKU","kind":"opening","quantity":30,"stock":30,"at":"2026-01-01T10:00:00+05:30"}]
```

Import before the generator establishes that product's opening balance; a second opening is rejected. Imported event provenance is server-owned `simulated-json-import`. Identical identities/payloads replay without new facts; changed payloads conflict and roll back the batch. Failed runs remain in operator history. Never use private staff data in this demo import.

Corrections retain the original sale, append one linked reversal and optionally a replacement, and require a reason and actor. The ADMIN API records the authenticated actor. A sale with dependent returns cannot be silently reversed. Completed ledger rows cannot be updated or deleted. A hard process crash leaves committed slots intact; a later run marks unfinished runs older than one hour interrupted.

Backup uses SQLite's consistent backup API and refuses to overwrite an existing output. To restore, stop the server and worker, keep the current database for investigation, copy the chosen backup to a **new** path, then pass that path to status/launch/worker. Do not copy a live database file directly or overwrite source data. On an older development database that lacks website tables, stop the worker before first launch so additive startup schema creation can finish; newly initialized databases include the observation table before generation starts.

## Hosted worker example (not deployed)

On a host with persistent `/srv/retailops-data`, run the same worker under the host's process supervisor, with restart-on-failure, from the project directory:

```text
/srv/retailops/.venv/bin/python -m app.live_demo worker --database /srv/retailops-data/seasonal.db --intraday --interval 30 --max-slots 100
```

Initialize the persistent database once before enabling the service. Keep the web process on the same host/disk for SQLite, configure authenticated HTTPS separately, restrict file permissions, and retain consistent backups. This is a deployment example, not a claim that a service is installed or running.
