# Candidate validation — October 25, 2026

Validated assembly: all sources in SOURCES.json, merge head bfe81dd, plus the integration change containing this report. Source model implementations and frozen research artifacts were not retuned. This is engineering verification, not real-world model acceptance.

- Full Python regression: **270 passed**, 69 upstream statsmodels/Pandas deprecation warnings, 55.39 seconds.
- Browser JavaScript checks: separated time windows, true zero/null handling; SSE parsing, authentication cleanup, request cancellation and network reconnection passed.
- Source guard: approved ancestry, eleven original agent implementations and their original archives preserved.
- New combined API checks: ADMIN bounded 100-event batches; STORE_MANAGER/ANALYST store isolation; HR denial; cursor continuation; unknown weather; no-store responses; expired and revoked tokens rejected by results, status and stream routes.
- Existing tests exercise missing/corrupt evidence and offline weather cache fallback. No live weather request was needed for this regression.
- Browser: signed-in combined dashboard loads verified frozen evidence and live unavailable state. At a 417-pixel viewport, the live panel has no document horizontal overflow (scrollWidth equals clientWidth). Disconnect hides protected results and restores the token form. Screenshot saved locally in validation-output/ml-dashboard/integrated-live-mobile.png.
- No supported viewport/emulated reduced-motion controls were exposed by the current browser tools. Wider desktop and device-specific interaction acceptance remains incomplete for this combined build; previous isolated dashboard desktop checks do not replace it. CSS retains keyboard focus styles and reduced-motion-aware entry animation; ECharts animation is disabled.

No real benchmark was downloaded, labels invented, heavy model weights fetched, stock fabricated, model promoted, or main branch changed. Simulator UI under prolonged load and a public webhook deployment are not validated by this local check. The local launcher is for research review, not production hosting.
