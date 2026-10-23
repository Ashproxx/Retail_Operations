# Dashboard validation

M19 PARTIAL. Five dashboard security/API checks pass; full regression 219 passed in 24.14 seconds. Covered authentication, HR denial, store isolation in every returned collection, global aggregate suppression, no-store responses, CSP, and corrupt/missing evidence failure.

Browser verification at localhost:8002/ml: terminal-token login; chain h=28 WAPE 13.56%, 56 observations, 80% coverage 67.86%, 95% coverage 85.71%; chart and table rendering; horizon switch to h=7 produces WAPE 13.47% and 14 observations; disconnect hides results. Desktop layout has no horizontal overflow. Screenshot saved locally under validation-output/ml-dashboard/dashboard-desktop.png (ignored, not committed).

Responsive CSS and reduced-motion behavior are implemented. Mobile viewport/browser verification remains unperformed because the current browser control exposes no viewport resizing capability. No claim of mobile acceptance is made. Live feed, feature importance and missingness dashboards remain pending; the isolated candidate explicitly says the live feed is unavailable. No change to the default launcher or production website.

Reports are checksum-checked local data exports, not merged source code. Their measured results retain synthetic/injected/descriptive labels, selection-before-test status, failures and exclusions. No model is promoted. Local file checksums do not protect against an administrator replacing both data and manifest.

Chart correction: time axes preserve elapsed dates and null breaks prevent lines across unscored windows. Genuine zero values remain zero; missing values remain null. Node assert-based regression passed; 5 dashboard API tests passed. Browser verified h=7 separated windows and unchanged metrics. Screenshot: validation-output/ml-dashboard/dashboard-gaps.png. Full suite was not repeated for this isolated chart-only correction.
