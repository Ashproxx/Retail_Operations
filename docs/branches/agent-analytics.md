# Conversational analytics

Owned: app/conversation/analytics.py and test_analytics.py. Legacy analytics is retained unchanged.
Interfaces: select_rows, statistics, analyze, diagnose, recommendations. Inputs are authorized catalog rows and validated context.
Measures: exact decimal revenue, units, ASP, category/family/location/product/gender/color/size/date groups, stock snapshots, stockout observations, sell-through proxy and comparison coverage.
Diagnostics: complete date coverage and nonzero baseline required for change claims; -20% declining, -40% low sales, +20% strong. Stock constraints take precedence. Seasonal causation is never inferred from calendar labels.
Recommendations: fact/analysis/advice separated; product, location, period and evidence supplied; no operational execution.
Tests: exact currency, stockout-vs-demand distinction, incomplete comparison, no-data state and rationale.
Checklist: [x] implemented [x] unit checked [x] integrated acceptance scenarios.
Limitations: observational heuristic, not causal attribution; missing fields and days remain unknown.
Knowledge delta: catalog -> analyze -> diagnostics -> recommendations; charts consume the same groups.

Integrated verification (2026-09-30): local Python suite and both real-browser gates passed. See `docs/conversation/VALIDATION.md` for tested scope and commit evidence. Feature checkpoints remain unchanged; this annotation belongs to the integration candidate.

Remote feature/checkpoint SHA: `b48be07849b00c0046826dd19bb14f8634fc1ab6`. Integration verification target: `c613603e503f675d9da2651d05e3af07438f54f1`; final CI evidence is recorded in `docs/conversation/VALIDATION.md`.
