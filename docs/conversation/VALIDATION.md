# Conversational candidate validation

Date: 2026-09-30. Repository: Ashproxx/Retail_Operations. Branch: `integration/conversational-retailops`.

## Scope and status

Recovered published commit `299126c6c2e1c3a75d9f01b3f13e1bc364f5dd76`. Its ledger and branch checklists were stale; this referenced report was missing. This checkpoint repairs those records and verifies the candidate locally. Updated remote CI now passes at c613603e503f675d9da2651d05e3af07438f54f1; all documented engineering gates are verified (100%). Status: READY FOR HUMAN REVIEW.

## Reproduced local checks

Windows, Python 3.12, disposable SQLite fixtures:

| Check | Result |
|---|---|
| `python -m pytest -q` | 201 passed, 0 failed, 0 skipped |
| `python -m pip check` | No broken requirements |
| `python scripts/check_branch_scope.py` | Approved ancestry; all 11 source implementations/archives preserved |
| `node scripts/check_dashboard.cjs` | Authenticated real API, filters, forecast, chat, feedback, audit, mobile layout and disconnect passed |
| `node scripts/check_conversation.cjs` | Progressive dialogue, all chart types, diagnostics, advice, competition, forecast, mobile overflow, token handling and reset passed |
| Screenshots | Desktop welcome and mobile conversation/forecast inspected; captures in ignored validation-output/ |
| `git diff --check` | Passed |

Browser scripts use Playwright and RETAILOPS_PYTHON to select the project interpreter. Temporary tokens are not saved in browser storage. No business writes run.

Corrections verified here:

- Declare tzdata for Windows IANA timezone support. Nine conversational tests failed before this fix.
- Compare Git blob hashes through clean filters so CRLF checkout conversion does not falsely report changed sources. Actual content changes still change hashes.
- Accept CRLF in both browser scripts' temporary-token parsing.
- Require explicit selection for duplicate product names; regression verifies selected-product totals.
- Include category/store peer averages, excluding the selected product, other locations and missing sales. Values are per observed product/store/day, not zero-filled histories.

## Published baseline CI evidence

[Run 36722933384](https://github.com/Ashproxx/Retail_Operations/actions/runs/36722933384) passed at `299126c6c2e1c3a75d9f01b3f13e1bc364f5dd76`. GitHub run status and individual steps were checked directly.

Both test and dashboard jobs succeeded: full Python suite, dependency check, source preservation, demo, Docker configuration/build, pinned pretrained retrieval evaluation, actual local Ollama inference, authenticated container/restart checks and both real-browser gates. This verifies the baseline, not remote execution of the corrections above.

## Acceptance coverage

1. Today's sales -> database locations -> Bandra -> totals -> graph choice -> interpreted chart: HTTP/browser gates.
2. Shirts -> category -> location/period -> sales, snapshots and history: service/HTTP/analytics tests.
3. Shorts not selling -> stock-aware diagnosis, forecast, competition, pricing/policy evidence: HTTP/browser gates.
4. What should we do about it? -> retained selection and evidence-led unexecuted advice: service/HTTP/browser gates.
5. Who competes with it? -> product choice, observed internal candidates and external-data limitation: competition/service/HTTP/browser gates.

## Agent, RAG and forecast status

Router/clarification, analytics, inventory, demand, pricing, supply, orders, customer service, returns and internal competition are integrated. Original agents and RAG remain preserved by the source guard. RAG ingestion, iteration bounds, sources and integrity are covered by the original suite. Conversational policy citation/audit composition is covered by HTTP tests. Actual model-backed retrieval and Ollama are measured separately in Linux CI.

Forecasts compare naive, moving-average, exponential and eligible weekly/weekday/yearly seasonal baselines on common chronological folds. MAE/RMSE select the model; zero-volume WAPE is unknown. Future-data perturbation tests prevent leakage. Calendar labels and heuristic bands are disclosed. This forecasts observed sales, not calibrated unconstrained demand.

## Limits and release boundary

No real business dataset was supplied. Demo/acceptance numbers are labelled synthetic; source mappings and actual accuracy require real-data validation. External competition is unconfigured. Parsing is bounded, similarity/diagnostic thresholds are heuristics, and missing attributes remain unknown. Run one server worker; in-memory scans/state coordination are intended for bounded local datasets.

No Azure deployment, commercial operation, main merge or main push occurred. Main was checked at `d39db70d0a8b429052340d691f01ca2769c1e8cc`. Review the candidate and obtain explicit human approval before merging into main.

## Final candidate CI and retained measurements

[Run 36731448837](https://github.com/Ashproxx/Retail_Operations/actions/runs/36731448837) completed successfully at `c613603e503f675d9da2651d05e3af07438f54f1`. Both jobs and their final step states were checked. Full tests, browser acceptance, Docker build/restart, model-backed retrieval and local Ollama inference passed.

The integration-validation artifact (11105612100) was downloaded and inspected. Exact reports: [container](measurements/container.json), [Ollama](measurements/ollama.json), [retrieval](measurements/retrieval.json). Container runs as UID 10001 and passed authentication, empty-database, scope-denial, persistence, memory and owned-feedback checks. Actual smollm2:135m inference returned a nonempty answer; factual accuracy is not certified. Retrieval ranked the correct source first on 12/12 authored positive queries, answered 8/12 and abstained on four positives plus both negative queries; scope leaks were zero. This tiny synthetic set does not establish production generalization.

The subsequent documentation-only savepoint records this result; application/test/dependency contents remain exactly those tested at `c613603e503f675d9da2651d05e3af07438f54f1`. Main merge still requires explicit human approval.
