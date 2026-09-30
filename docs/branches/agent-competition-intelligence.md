# Internal competition intelligence

Owned: competition.py, config/competition.json and test_competition.py.
Inputs: authorized observations, current product/location/period; Product 360 labels.
Outputs: internal candidates, explained weighted similarity, observed coverage, relative units/revenue/price/stock, explicit external-data limitation.
Weights: category .35, family .15, gender .10, color .05, price proximity .20, store overlap .15. Only observed factors are normalized; no learned substitution probability claimed.
Tests: observed family restriction, missing attributes, relative units and external-data disclosure.
Checklist: [x] implementation [x] tests [x] documented score [x] conversational deep-dive verification.
Limitations: no external feed; no causal claim from higher sales. Incomplete attributes reduce coverage.
Knowledge delta: Catalog + Product360 -> internal similarity -> competition evidence -> deep-dive response.

Integrated verification (2026-09-30): local Python suite and both real-browser gates passed. See `docs/conversation/VALIDATION.md` for tested scope and commit evidence. Feature checkpoints remain unchanged; this annotation belongs to the integration candidate.

Remote feature/checkpoint SHA: `b65e8be0ab09ed8bb20cd52fb2087a55782bee7c`. Integration verification target: `c613603e503f675d9da2651d05e3af07438f54f1`; final CI evidence is recorded in `docs/conversation/VALIDATION.md`.
