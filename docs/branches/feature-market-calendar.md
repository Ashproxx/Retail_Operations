# Market calendar

Purpose: explicit market/timezone and natural-language date periods.
Owned: dates.py, config/market_calendar.json, test_dates.py.
Interfaces: resolve, today, comparison, season. Inclusive dates; week starts Monday; last N days includes today.
Inputs: configured market, server clock, observed date bounds. No IP location or inferred festival dates.
Tests: India/UTC midnight, weeks, months, quarters, invalid ranges and calendar events.
Checklist: [x] implementation [x] boundary tests [x] configuration [ ] integrated conversational verification.
Limitations: broad India season profile; no weather feed or empirical causal claim.
Baseline: taxonomy 1b8b360; integration consumes date contracts without modifying agent source branches.
Knowledge delta: market JSON -> dates -> slot filling / forecast context.
