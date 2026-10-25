# Isolated real-time candidate (M16)

Start from the existing imported source database, preferably a SQLite backup under `.retailops/realtime-candidate/retailops.db`. No source transaction is changed by this extension. Only new sales_events and weather_hourly tables receive data. This branch does not merge the ML core or change normal enterprise startup.

```powershell
$env:RETAILOPS_WEATHER_ENABLED='true'
$env:RETAILOPS_STREAM_MODE='simulator'
$env:RETAILOPS_STREAM_SPEED='5'
.venv/Scripts/python.exe -m app.realtime.launch --database .retailops/realtime-candidate/retailops.db --port 8001
```

Normal default is stream off and weather disabled. The isolated launcher retains terminal-generated bearer login. `GET /api/realtime/status` and `GET /api/stream/sales` require bearer auth; the latter is server-sent events and rechecks auth on each poll. Use an authenticated fetch stream, not a token in the URL. `after` resumes by event ID; `once=true` returns a finite page of up to 100 rows. IDs are global monotonic cursors, but only authorized stores' data is returned.

Status fields: mode/task status, latest authorized event, events received in the last minute, received-by-cutoff 15-minute/hour totals, same-hour-last-week comparison, source labels, latest observed weather and freshness. Empty event coverage produces null units, not zero. Mixed real/synthetic source labels remain visible. No intraday forecast adjustment is claimed before M17/M20 integration. M19 owns the visible dashboard card.

Simulator resamples supplied workbook transaction distributions using a seed, shifts transaction/delivery dates, marks every row synthetic-stream, and emits at requested 1–1000x pacing (actual throughput depends on the machine). One run is bounded to 86,400 events. Restart creates a new timestamped run identity. A fixed seed and start reproduce the exact events. It never updates sales_transactions. Do not present these events as live retailer sales.

## Weather approval and provenance

On 2026-10-23 the user approved reviewing terms and enabling weather if suitable. The current free API permits educational/non-commercial use, within its published rate limits. API data require CC BY 4.0 attribution and a link beside displayed weather. Sources actually reviewed:
- https://open-meteo.com/en/terms
- https://open-meteo.com/en/licence
- https://open-meteo.com/en/docs/historical-weather-api

Calls send coordinates, date/range controls and variable names only, never retail or employee records. HTTPS host allowlist, disabled redirects, timeout, three attempts, exponential backoff, one-hour cache and one-minute failed-request cooldown are implemented. Last successful stored readings remain readable after failures; age and fetch failure are shown separately. Provider errors do not block offline startup. Reanalysis is not a historically available forecast; do not leak future observed weather into a backtest.

```powershell
.venv/Scripts/python.exe -m scripts.backfill_weather --database .retailops/realtime-candidate/retailops.db
```

An explicit backfill was completed for 2025-09-29 through 2026-09-29 (366 inclusive UTC dates): all 8,784 hourly values for the three requested variables were present. Receipt: WEATHER_BACKFILL.json. UTC date boundaries must be converted explicitly when joining local Asia/Kolkata days; this receipt is not a claim of 366 complete local-midnight day windows. Store source, fetched_at, observed_at and synthetic=false. Availability at fetch time is preserved; reanalysis is not a forecast vintage.

## Webhook contract

Set stream_mode=webhook and a private HMAC key at least 32 characters long. POST /api/stream/ingest body is `{ "payload": <exact Sales_Transactions column mapping>, "synthetic": false }`. Require ADMIN or authorized STORE_MANAGER bearer grant. Sign the exact raw body with SHA-256 HMAC over `timestamp + '.' + body`; headers are X-Event-Timestamp (Unix seconds) and X-Event-Signature (hex). Timestamps must be within five minutes. Bodies over 64 KiB, invalid signatures, unknown stores/SKUs, invalid amounts, future events or conflicting repeated txn_id are rejected. Identical repeats are idempotent; old or out-of-order event times are accepted with separate current received_at.

Keep the HMAC key outside Git. This is a one-worker prototype: the lock and background tasks are process-local. Kafka or Azure Event Hubs is a future scale-out option, not installed now. The application still requires a properly authenticated upstream POS; a valid signature is not independent proof that the input represents genuine sales.
