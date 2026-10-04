# Decisions

- 2026-09-28: User selected Retail_Operations. Use the existing verified dashboard baseline, not the other repository named in the PDF.
- Main currently points to d39db70d0a8b429052340d691f01ca2769c1e8cc; it changed outside this work and will remain untouched.
- Preserve the old release candidate. New integration target: integration/conversational-retailops.
- Local-first; no Azure deployment, paid infrastructure or external competitor scraping.
- Database-derived options and deterministic calculations precede optional language-model interpretation. Unsupported language asks a useful clarification rather than fabricating facts.
- Real dataset absent: retain and label showcase fixtures; implement imports and validation without claiming real business validation.

- 2026-09-30: Continue the existing integration branch. Verify earlier CI directly, not from pasted claims. Integration-owned corrections preserve original agent branches. Declare timezone data for Windows; compare source through Git clean filters.

## Phase 3

2026-10-03: User authorized Phase 3 website upgrade and new component. Continue Retail_Operations as previously selected; PDF Retail_Ops reference is superseded. Supplied workbooks found in Downloads and audited. Synthetic source records stay local, not in Git. Import actual files; never replace them with a tiny generated fixture for acceptance. Models 3/4 remain Coming Soon. Reuse Python/FastAPI/SQLAlchemy/ECharts. Main stays read-only.

2026-10-04: Full supplied-workbook reconciliation and browser acceptance passed. Integration candidate composes sequential owned checkpoints. CI exercises disposable fixtures because source files are intentionally local; its results do not replace actual workbook acceptance. Hardened name matching to retain every supplied name token and reject unsupported individual-sales attribution. No new dependency or original source-agent modification was required.
