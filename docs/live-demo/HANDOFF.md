# RetailOps delivery handoff - 2026-10-30

The local engineering work for the seasonal demo and integrated research candidate is delivered on `codex/live-seasonal-dataset`. This is **not full research/PDF acceptance**. The tested implementation is `f50bc4d5c4fde9aa9215bd922531ce7ec5fba147`; later delivery documentation does not change runtime code. Its approved integration base is `d554f3967e14f9cb720f8caf3915af83419ec8be`.

## Run and recover

From the repository root, after the existing virtual-environment setup:

```powershell
.venv/Scripts/python.exe -m app.live_demo launch --database .retailops/live-seasonal/retailops.db --port 8003
.venv/Scripts/python.exe -m app.live_demo worker --database .retailops/live-seasonal/retailops.db --intraday --interval 30 --max-slots 100
```

Run these in separate terminals, checking for existing processes first. Open `/models`, `/retail`, `/employees`, `/assistant` or `/ml` on localhost:8003 and use the temporary token printed by that launcher. Tokens are not saved here. The web server and generator are separate processes. The server started for the user remains available; the worker was not started by the final acceptance run. This is simulated stock/staff activity, not verified real inventory or employees. Neither process runs while the computer is off.

See [README](README.md) for initialization, configuration, import, correction and consistent backup/restore commands. Restore to a new database path with server/worker stopped; retain the original for investigation. Unknown observations remain unknown; immutable ledger corrections append linked entries.

For the separate realtime resampler, use a consistent **copy of the original imported database**, not the seasonal mixed projection:

```powershell
.venv/Scripts/python.exe -m app.ml_dashboard.launch --database PATH_TO_IMPORT_COPY --port 8002 --stream-mode simulator
```

Its synthetic events live in a separate event table and do not update historical sales or frozen scores. Weather is off by default. The final temporary acceptance server on 8002 was stopped. Only the already-approved coordinate-only weather option may make public weather requests; no private records may leave this computer.

## Reproduce engineering checks

```powershell
.venv/Scripts/python.exe -m pytest -q --disable-warnings
node tests/live_demo/demo-refresh.test.cjs
node tests/live_demo/dataset-refresh.test.cjs
node tests/ml_dashboard/chart-data.test.cjs
node tests/ml_dashboard/live.test.cjs
.venv/Scripts/python.exe scripts/check_branch_scope.py
```

Recorded result: **293 passed**, 69 dependency warnings, 62.36 seconds; four JavaScript suites and source guard passed. [Validation](VALIDATION.md) records browser checks, 310-slot/three-process concurrency, backup/restore, two retained-database restart cycles, corrections, exports, mobile/desktop widths, keyboard disclosures, all six research questions and actual synthetic-stream arrivals. These are bounded local checks, not a production soak or Linux CI result.

## Remaining acceptance gates

- Human-reviewed router and similarity labels, actual policy retrieval judgments and natural anomaly validation. Draft/injected/fictional fixtures cannot substitute for these.
- A permitted independent retail benchmark. A prior automatic approval block was not bypassed; no dataset was downloaded for this handoff.
- Historical forecast vintages and genuine inventory/lead-time outcomes for time-safe weather ablation and operational benefit. Current observations and simulated stock do not supply this evidence.
- The original master prompt's universal criteria referenced by the Astra addendum remain unavailable. The supplied seasonal prompt does not establish those older criteria.
- A current Linux CI run. WSL is not installed; existing workflow push filters omit this development branch. The old workflow also downloads model weights, which this delivery did not trigger. A permitted runner/workflow must be established before claiming M20 fully accepted.

M17 final-test labels have already been opened. Do not retune on them or rebrand a repeat as independent accuracy. Frozen chain h=28 weekday baseline WAPE is 13.5636%; its nominal 80% interval covered only 67.86%. No model is promoted. Delivery candidates did not beat the prevalence baseline on Brier score. Price/feature associations are not causal effects. Detailed metrics and reproduction protocols remain in [scorecard](../ml/AIML_SCORECARD.md) and the linked frozen reports.

Main and `integration/dual-model-retailops` are preserved. No cloud deployment, paid service, external private-data transfer or new model-weight download was performed. The next work should follow new evidence or a resolved runner/criteria gate rather than repeatedly regenerating synthetic results.
