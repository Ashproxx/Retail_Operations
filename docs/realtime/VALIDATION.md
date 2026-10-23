# M16 validation evidence

2026-10-23: 217 full-suite tests passed on this branch (214 inherited, 3 real-time tests). Targeted tests cover mocked offline weather and cache/fallback, host rejection, deterministic simulator, late/out-of-order/idempotent ingestion, conflicting identities, scoped access, invalid signatures, SSE and status authorization. No new dependencies installed.

Live candidate on loopback port 8001 returned authenticated status 200 and finite SSE 200. Both weather freshness and synthetic-event freshness were green. The status explicitly labelled events synthetic-stream. Weather requested only coordinates and public variable/range controls. Hosts contacted for weather: api.open-meteo.com and archive-api.open-meteo.com. Metadata-only backfill receipt confirms 8,784/8,784 hours. Source showcase DB was backed up before candidate use; it was not changed.

Normal application startup still uses app.enterprise.launch; real-time lifespan composition is opt-in via app.realtime.launch. No visible live dashboard or joined ML accuracy is claimed here. The existing branch guard is not changed on this branch; its approved extension lives on platform/ml-core. No remote Linux CI verification or M20 integration is claimed.
