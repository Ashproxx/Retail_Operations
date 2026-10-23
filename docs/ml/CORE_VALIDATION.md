# M15 validation

Baseline-only framework, 2026-10-23. No final test labels were scored and no trained ML accuracy is claimed.

- Five dedicated tests pass: numerical baseline parity and registry corruption/round-trip; post-cutoff perturbation and missing-day alignment; embargo/test-block isolation; statistics, importance and monitoring; SQL role/store restrictions.
- Real imported source run: five chain baselines reproduce the existing last-28-day one-step calculation exactly, through 2026-08-04 only. Four embargoed validation origins and horizons 1/7/14/28 are recorded. Scorecard output is validation-only, with all six independent-test claims marked UNVERIFIED.
- Source-preservation branch guard passes with the labelled M15 shared branch-name delta.
- The full regression result is recorded in the commit completion report. No new libraries were installed; no external models downloaded.

Run `python -m scripts.ml_run --config configs/ml_baseline.yaml`, `python -m scripts.ml_report`, `python -m pytest tests/ml -q`, and `python scripts/check_branch_scope.py`.

Registry JSON is executable-code-free and checksummed for corruption, not cryptographically authenticated against malicious replacement. Keep it in trusted local storage. Monitoring thresholds are documented heuristics. Weather, covariate adapters, conformal calibration and trained forecasting families belong to subsequent milestones. Pure baselines expose no invented quantiles. Local experiment logs and model artifacts are ignored by Git.

M14 is isolated on docs/ml-methodology@e8f8280. Global graph regeneration and integration into the website are not performed. Inherited universal acceptance/remote CI remain unverified, so implementation evidence is not a claim of extension completion.
