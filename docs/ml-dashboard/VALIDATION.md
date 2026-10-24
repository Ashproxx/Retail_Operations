# Dashboard validation

M19 PARTIAL. Five dashboard security/API checks pass; full regression 219 passed in 24.14 seconds. Covered authentication, HR denial, store isolation in every returned collection, global aggregate suppression, no-store responses, CSP, and corrupt/missing evidence failure.

Browser verification at localhost:8002/ml: terminal-token login; chain h=28 WAPE 13.56%, 56 observations, 80% coverage 67.86%, 95% coverage 85.71%; chart and table rendering; horizon switch to h=7 produces WAPE 13.47% and 14 observations; disconnect hides results. Desktop layout has no horizontal overflow. Screenshot saved locally under validation-output/ml-dashboard/dashboard-desktop.png (ignored, not committed).

Responsive CSS and reduced-motion behavior are implemented. Mobile viewport/browser verification remains unperformed because the current browser control exposes no viewport resizing capability. No claim of mobile acceptance is made. Live feed and missingness dashboards remain pending; the isolated candidate explicitly says the live feed is unavailable. No change to the default launcher or production website.

Reports are checksum-checked local data exports, not merged source code. Their measured results retain synthetic/injected/descriptive labels, selection-before-test status, failures and exclusions. No model is promoted. Local file checksums do not protect against an administrator replacing both data and manifest.

Chart correction: time axes preserve elapsed dates and null breaks prevent lines across unscored windows. Genuine zero values remain zero; missing values remain null. Node assert-based regression passed; 5 dashboard API tests passed. Browser verified h=7 separated windows and unchanged metrics. Screenshot: validation-output/ml-dashboard/dashboard-gaps.png. Full suite was not repeated for this isolated chart-only correction.


## Supplemental evidence panel

Admin-only feature-importance and quantile checks now read the pinned M17 supplement at 7ad9a4a. The panel explicitly labels the fourteen-day exploratory validation window and retains negative feature-importance values. Global chain evidence is omitted entirely from manager/analyst responses. Existing frozen test charts are unchanged. Re-run the local export script to add supplement.json; missing/corrupt evidence still fails closed.

Five dashboard API tests passed, including supplement suppression for scoped roles and ADMIN access. JavaScript syntax check passed.

Desktop supplement acceptance completed on 2026-10-24 at localhost:8002/ml: terminal-token login displayed all eleven feature rows, including lag_1 = -11.74; quantile and conformal 80% coverage were both 100.00%, with widths 134.54 and 139.00 units. The fourteen-day exploratory label and limitations were visible. Disconnect removed the results from the accessible page. Screenshot saved locally as validation-output/ml-dashboard/dashboard-supplement.png (ignored). Full regression: 219 passed in 41.84 seconds. Mobile acceptance remains unperformed; live wiring still awaits M20 approval. No model is promoted.


## Malformed evidence handling

The shared store-scope filter now rejects non-object evidence rows with the existing unavailable-report response (503), even when a local manifest checksum matches. Previously a null row raised an unhandled attribute error. Regression covers ADMIN, STORE_MANAGER and ANALYST and preserves fail-closed behavior. Six focused dashboard tests passed; full regression 220 passed in 23.27 seconds. No browser rendering changed, so visual tests were not repeated.


## Scoped observation coverage

Added an imported-data coverage panel backed by existing authorized retail SQL filters. Its 28-day window ends at the latest sale in the caller's own scope, so another store cannot leak its dates. Days without transactions remain unknown (null); explicitly recorded zero quantity stays zero. Empty scope returns no observations, not fabricated zero sales. Store aggregation does not establish complete imports, closure, stock or current live freshness. No M16 source or stream is integrated.

Eight focused dashboard checks passed, including a later private-store date, zero versus missing values and empty history. Full regression: 222 passed in 23.06 seconds. Desktop browser verified September 2-29 snapshot, twenty admin store rows and one unknown day for ST02/ST15/ST18/ST20; disconnect clears the panel. Local screenshot: validation-output/ml-dashboard/dashboard-coverage.png. Mobile acceptance remains open.
