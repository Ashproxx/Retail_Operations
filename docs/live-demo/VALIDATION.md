# Live seasonal checkpoint — 2026-10-28

This is an engineering checkpoint, not complete acceptance of either PDF and not real-world ML evidence.

- Full regression: **283 passed**, 69 upstream warnings, 53.42 seconds. Focused demo suite: 13 tests, including fresh-process website schema registration and correction replay counts. Source/branch preservation guard passed.
- Fixed missing website observation-table registration during initialization, preventing new databases from needing that DDL when a worker already holds a write lock. Existing development database startup was verified with the worker stopped, then the worker was started successfully.
- Moved worker heartbeat writes inside the same retry handling as generation so a contending writer does not terminate the worker before its retry path.
- Corrections now report actually inserted versus replayed rows in run history. Repeated corrections preserve the original and add no duplicate reversal.
- Local retained database before catch-up: 88,407 sales facts, 88,670 ledger rows, 12 synthetic staff, 4,011 shifts and 7,806 attendance records. Imported coverage is 2025-09-29 through 2026-09-29; synthetic history begins 2024-10-01 and deliberately skips that imported interval.
- Real local worker catch-up committed **16 slots / 40 events** with run ID `4949e3c52d274facbab3ab75e22625f9`. Website status changed from worker-stopped/stale to running/fresh. Today displayed 17 simulated net units and INR 22,150.35; known inventory changed from 709 to 671 units across 24 pairs. These are demo values, not accuracy measurements.
- Browser sign-in, committed updates, 30-day selection and disconnect were exercised. Thirty-day selection displayed 1,100 net units / INR 1,287,190.62. The live panel was removed on disconnect. At requested viewport widths 390 and 1440, document scroll width equalled client width (375 and 1425 after scrollbar allocation). This verifies no document horizontal overflow, not complete visual/accessibility acceptance.

## Remaining acceptance work

Recovery follow-up: the real backup CLI was exercised against a partially generated temporary database, an overwrite attempt was refused without changing backup bytes, and both restored/original databases resumed to identical event identities, amounts and stock movements. Restored integrity/foreign-key checks passed with 40 distinct checkpoints. A backdated second opening could previously bypass the as-of check and inflate stock; opening validation now rejects any existing opening for that store/SKU, including later-dated ones, within the serialized writer transaction. Regression covers rollback and unchanged facts. Focused demo suite: **15 passed in 8.23 seconds**. The prior full-suite count above predates these two added tests; it was not rerun for this isolated change.

- Finish detailed PDF-to-implementation coverage review, including UI race/pagination automated checks, end-to-end backup/restore and prolonged concurrency. Existing Python tests cover crash rollback, restart equivalence, two workers, source preservation, scope, historical arrival cutoffs, immutable stock and invalid returns.
- Review the existing catalog/employee overview labels for the demo context: they still describe snapshot provenance and catalog counts. The new Daily operations panel contains live signed inventory and actual simulated attendance; do not call the catalog pie an on-hand inventory pie.
- Complete visual chart/keyboard checks, staff-page interaction and export verification. No hosted service has been deployed. Local worker/server availability depends on this computer remaining on.
- The calendar is deliberately empty: named festival dates are not verified. Missing years omit effects with a visible warning. Source catalog and sales provenance remains unverified.
- Earlier M17/M18 research reports remain frozen; human labels, genuine independent benchmarks and historical weather-forecast vintages remain evidence gates. Synthetic seasonal data must not be used to erase those limitations.

Development remains on `codex/live-seasonal-dataset`; main and the original showcase branch are unchanged. See README for initialization, worker, correction and recovery commands. Local databases and temporary tokens are not committed.
