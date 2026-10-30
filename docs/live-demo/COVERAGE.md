# PDF acceptance map

Reviewed against the six-page Live Seasonal Dataset prompt and the nineteen-page Astra addendum on 2026-10-28. This map distinguishes implementation from remaining acceptance; it is not a declaration that both PDFs are complete.

| Live dataset requirement | Implementation / evidence | Remaining acceptance |
| --- | --- | --- |
| Isolated persistent data and safe source snapshot | `store.initialize`, whitelist import, SQLite backup; source-preservation test | Retained source checksum unchanged across two real website/generator restart cycles; see VALIDATION.md |
| Integer money, dates, provenance, immutable stock | `schema.sql`, `store.append`; conservation, foreign-key, return-limit and opening tests | None identified in this bounded local scope |
| Replays, conflicts, corrections and retained originals | Source/identity uniqueness, digest conflicts, linked reversal/replacement, failure history | Authenticated correction sequence verifies original retention, KPI/chart/stock deltas and replay; see VALIDATION.md |
| Backup, restore and offline catch-up | Real backup CLI test; independent resumed databases match; overwrite refused | No hosted disaster-recovery claim |
| Versioned seeded generation and simultaneous workers | Saved configuration/checkpoints; 310-slot three-process comparison, different hash seeds and batch sizes | Production soak/load testing is outside measured evidence |
| Seasonality, campaigns and limited stock | Monthly actual-category weights, weekly factors, dated optional events, Gamma-Poisson variation, replenishment/returns/lost demand | Calendar intentionally empty; named festival dates need verified or explicitly supplied assumptions |
| Synthetic staff and attendance | Synthetic profiles, nonoverlapping daily shifts, weekly rest days, absence and due clock-out | Profiles are immutable bootstrap identities; effective-dated profile edits are not exposed or claimed |
| Existing website, live stock and current staff | Existing dataset cards and Daily operations panel; actual browser and export checks in VALIDATION.md | Demo workspace source copy corrected; category charts, keyboard disclosures and desktop/mobile layouts verified |
| Historical ranges, source filters, freshness and pagination | Scoped summary/events/staff/runs APIs and polling; frontend request-interleaving checks | Category selection and retained audit disclosure verified in browser; restart and correction readouts verified separately through actual processes/API |
| Historical knowledge time | Ledger arrival-cutoff API excludes later corrections | Any new training on this demo must use an explicit arrival cutoff; existing frozen ML evidence is not retrained against this mutable projection |
| Configuration and operator lifecycle | JSON configuration, sample `.env`, init/backfill/run-once/worker/status/launch/backup/import/correct commands, README | Local services only; no hosted deployment |

## Earlier Astra addendum

M14/M15 methodology and ML infrastructure, M16 stream/weather implementation, and the integrated ML dashboard are retained from `integration/ml-realtime-candidate` at `d554f3967e14f9cb720f8caf3915af83419ec8be`. Consult `docs/ml-integration/VALIDATION.md`, `docs/ml/M17_PROGRESS.md`, and `docs/auxiliary/VALIDATION.md` for dated evidence rather than treating the original scorecard's early checkpoint wording as a new result.

The forecasting final test blocks were already opened. Baseline h=28 WAPE 13.5636% and 80% interval coverage 67.86% remain synthetic-workbook findings, including undercoverage. Later quantile/importance and pooled supplements are development evidence; they do not replace that untouched-test comparison. No complex model has been promoted by this seasonal dataset work.

Human-reviewed routing and similarity labels, a permitted independent real benchmark, and time-appropriate historical weather forecast vintages remain unavailable. Retrieval/anomaly/price supplements have their own limited protocols and do not establish real-world accuracy or causal effects. Never fill these gaps with synthetic seasonal records and relabel the results as real.

The scorecard was reconciled without changing frozen model selection. All six research questions now share scoped evidence between assistant and dashboard and were exercised in both browser interfaces. Combined streaming against an isolated original-import copy was verified on 2026-10-30, alongside 293 passing tests. The seasonal launcher deliberately has no separate realtime resampler. Main and the original showcase remain unchanged. See HANDOFF.md for human evidence, original-criteria and Linux CI gates; full PDF acceptance is not claimed.

CI configuration inspection: `.github/workflows/ci.yml` has push triggers for three older integration branches, not this seasonal branch or `integration/ml-realtime-candidate`; pull requests also trigger it. No successful hosted run for the current seasonal commit is established here. Its optional embedding/Ollama downloads were not run. Local Python, browser-request and source-preservation checks are reported separately and must not be described as hosted CI success.
