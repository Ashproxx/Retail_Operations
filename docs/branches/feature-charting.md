# Chart specifications

Owned: app/conversation/charts.py and test_charts.py. Frontend renderer belongs to feature/conversational-ui.
Interfaces: compatible(group_by, rows), specification(rows, context).
Supports category bar/horizontal bar/pie/doughnut, time line/area/bar, multi-store grouped/stacked/multi-line/heatmap, price-units scatter where data exists.
Rules: metric, period and compatible chart type required. Null observations remain null. Same deterministic aggregation as textual analysis; every spec includes interpretation, sources and synthetic label.
Tests: exact chart totals, share interpretation and incompatible chart rejection.
Checklist: [x] backend specs [x] unit tests [x] renderer [x] browser interaction.
Limits: category groups capped at 30, time points at 366; ask to narrow rather than silently misrepresent shares.
Knowledge delta: analytics groups -> typed chart spec -> frontend chart library -> text interpretation.

Integrated verification (2026-09-30): local Python suite and both real-browser gates passed. See `docs/conversation/VALIDATION.md` for tested scope and commit evidence. Feature checkpoints remain unchanged; this annotation belongs to the integration candidate.
