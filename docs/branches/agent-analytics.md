# Conversational analytics

Owned: app/conversation/analytics.py and test_analytics.py. Legacy analytics is retained unchanged.
Interfaces: select_rows, statistics, analyze, diagnose, recommendations. Inputs are authorized catalog rows and validated context.
Measures: exact decimal revenue, units, ASP, category/family/location/product/gender/color/size/date groups, stock snapshots, stockout observations, sell-through proxy and comparison coverage.
Diagnostics: complete date coverage and nonzero baseline required for change claims; -20% declining, -40% low sales, +20% strong. Stock constraints take precedence. Seasonal causation is never inferred from calendar labels.
Recommendations: fact/analysis/advice separated; product, location, period and evidence supplied; no operational execution.
Tests: exact currency, stockout-vs-demand distinction, incomplete comparison, no-data state and rationale.
Checklist: [x] implemented [x] unit checked [ ] integrated acceptance scenarios.
Limitations: observational heuristic, not causal attribution; missing fields and days remain unknown.
Knowledge delta: catalog -> analyze -> diagnostics -> recommendations; charts consume the same groups.
