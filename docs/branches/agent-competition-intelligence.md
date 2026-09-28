# Internal competition intelligence

Owned: competition.py, config/competition.json and test_competition.py.
Inputs: authorized observations, current product/location/period; Product 360 labels.
Outputs: internal candidates, explained weighted similarity, observed coverage, relative units/revenue/price/stock, explicit external-data limitation.
Weights: category .35, family .15, gender .10, color .05, price proximity .20, store overlap .15. Only observed factors are normalized; no learned substitution probability claimed.
Tests: observed family restriction, missing attributes, relative units and external-data disclosure.
Checklist: [x] implementation [x] tests [x] documented score [ ] conversational deep-dive verification.
Limitations: no external feed; no causal claim from higher sales. Incomplete attributes reduce coverage.
Knowledge delta: Catalog + Product360 -> internal similarity -> competition evidence -> deep-dive response.
