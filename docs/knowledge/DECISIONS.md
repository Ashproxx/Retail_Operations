# Decisions

- 2026-09-28: User selected Retail_Operations. Use the existing verified dashboard baseline, not the other repository named in the PDF.
- Main currently points to d39db70d0a8b429052340d691f01ca2769c1e8cc; it changed outside this work and will remain untouched.
- Preserve the old release candidate. New integration target: integration/conversational-retailops.
- Local-first; no Azure deployment, paid infrastructure or external competitor scraping.
- Database-derived options and deterministic calculations precede optional language-model interpretation. Unsupported language asks a useful clarification rather than fabricating facts.
- Real dataset absent: retain and label showcase fixtures; implement imports and validation without claiming real business validation.

- 2026-09-30: Continue the existing integration branch. Verify earlier CI directly, not from pasted claims. Integration-owned corrections preserve original agent branches. Declare timezone data for Windows; compare source through Git clean filters.
