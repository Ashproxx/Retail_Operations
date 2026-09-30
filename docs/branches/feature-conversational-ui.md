# Conversational interface

Branch: `feature/conversational-ui`; parent: integrated authenticated conversation API.

Owns `app/conversation/static/`: same-origin chat UI, accessible choice buttons and data tables, local Apache ECharts 5.6.0 renderer, forecast and comparison displays, responsive desktop/mobile layout. Credentials live only in page memory. All content is created with textContent; chart tooltips use richText rather than HTML.

The API owns permissions, context, calculations and provenance. The UI sends only user turns and opaque selected option values. No role or store authority is client-controlled. Old `/dashboard` remains available.

Validation: `scripts/check_conversation.cjs` tests the real server, progressive selection, charts, forecasting, recommendations and mobile overflow. Python API tests cover access control and evidence consistency. See the integration milestone ledger for executed results.

Limitations: no external competitor feed; no real dataset supplied. Synthetic data is prominently labelled. Voice input, attachments and operational write actions are not claimed.

Vendor: Apache ECharts 5.6.0, Apache-2.0, retained license in static/vendor. No CDN or Node installation is needed to run the website.

Integrated verification (2026-09-30): local Python suite and both real-browser gates passed. See `docs/conversation/VALIDATION.md` for tested scope and commit evidence. Feature checkpoints remain unchanged; this annotation belongs to the integration candidate.

Remote feature/checkpoint SHA: `b1d0a7ad32877a65b17ec82899a794b9cd456c12`. Integration verification target: `c613603e503f675d9da2651d05e3af07438f54f1`; final CI evidence is recorded in `docs/conversation/VALIDATION.md`.
