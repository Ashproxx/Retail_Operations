# M20 integration plan - NOT AUTHORIZED / NOT EXECUTED

Do not create or merge the integration candidate until the human approves exact source commits and the base. Main and integration/dual-model-retailops remain protected. This plan is not an approval request during the unattended window and is not evidence of acceptance.

Proposed base: integration/dual-model-retailops@c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. Proposed candidate name: integration/ml-realtime-candidate.

## Exact source checkpoints

| Branch | Commit |
|---|---|
| docs/ml-methodology | e8f8280caa98d4a8f1bb504b64bc864699c9e7ed |
| platform/ml-core | ca22a9f755504de656093eba1f026c6aee620efa |
| platform/realtime-data | c944c3edb03eb98fcbb451096a47bb5d5bbc34f9 |
| ml/forecasting-models | c35c0cab0d4df2742ce4b39cb53f833cbfef9b9e |
| ml/auxiliary-models | aa9bdd0c538af7a80eb99522d2f826930138f8f9 |
| ui/ml-dashboard | f492adffdb0a774442e9a4c53a960602e0cb2274 |

## Assembly and verification after approval

1. Recheck clean working tree, remote refs, dependencies and approval scope. Preserve unrelated local files. Create candidate from the approved base; never use main as a workspace.
2. Bring in methodology, ML core and real-time source checkpoints. Forecasting already descends from ML core; do not duplicate or overwrite that dependency. Auxiliary and dashboard descend independently from the showcase base. Resolve branch-record overlaps by archiving source records and writing a new integration record; do not lose inherited acceptance evidence.
3. Compose explicit mount hooks in one candidate launcher. Keep the standard terminal token behavior. Bind local-only by default. Keep all current authentication, store scope, audit and baseline fallback paths.
4. Replace offline dashboard evidence loading only with a documented scoped service contract; preserve the frozen benchmark display separately from live predictions. Integrate M16 freshness and SSE only after route and store-scope tests. Historical ERA5 data cannot be used as if it were an archived forecast.
5. Do not promote M17 candidates automatically. Delivery candidates failed the Brier comparison; keep descriptive delivery reporting. Use model/registry versions and baseline fallback explicitly. Models must never execute pricing, hiring, inventory or other business actions.
6. Run full regression, source-preservation checks, role/store API isolation, expired/revoked-token and reconnect checks, corrupt/missing artifact behavior, offline/weather-failure fallback, freshness and bounded stream checks. Complete desktop and mobile browser acceptance, keyboard and reduced-motion checks.
7. Publish an exact-commit validation report and source manifest, then seek separate approval for any release action. No main merge or production deployment is implied.

## Unresolved acceptance gaps

M17: store/category pooling remains blocked by missing observations; store-level pooled development comparison is complete. Broader independent quantile/feature-importance evaluation, forecast-vintage weather/festival ablation, real benchmark and independent review remain open. The synthetic test is already opened: future tuning cannot claim independence by reusing it. Calibration undercoverage must remain visible.

M18: human-reviewed router labels and natural-query RAG benchmark, natural anomaly labels beyond the completed injected seasonal comparison, human similarity relevance and genuine stock/lead-time labels remain open. Price association with uncertainty and geometric ranking agreement are measured; neither establishes causality or semantic relevance. Current metrics are synthetic, descriptive or injected proxies only.

M19: actual live panels, broader importance evidence and mobile browser acceptance. Current separate launcher serves /ml at port 8002 and does not modify the default website.

These are partial checkpoints, not M17-M20 completion. No real-world accuracy or universal acceptance claim is justified.

Latest supplemental development measurements and draft router/retrieval diagnostics do not satisfy independent accuracy or human-review gates. The new importance panel passed desktop browser verification on 2026-10-24; full regression passed 219 tests. Mobile acceptance remains open.

## October 24 evidence handoff

- Forecasting c35c0ca: 236 tests passed. Pooled boosting mean store WAPE 40.1802%, baseline 40.2994%; only six of thirteen stores favor pooling. Seven stores and 120 store/category series excluded; no promotion.
- Auxiliary aa9bdd0: 234 tests passed. Descriptive log-price coefficient -0.2484, week-cluster interval [-0.3862, -0.1106]; no causal interpretation. Geometric top-five overlap 0.743529 and Spearman 0.795624; 534 review pairs have blank human labels.
- Dashboard f492adf: 219 tests passed and desktop supplement verified. The current export still intentionally pins earlier primary/quantile data artifacts; these new supplemental results are not yet displayed. Updating this plan does not merge code or imply M20 approval.

Public benchmark preparation encountered an automatic approval rejection while writing its protocol. The rejection gave only "blocked by policy"; no download or scoring occurred. Do not bypass that rejection or describe the public benchmark as complete. Independent dashboard work can continue.

Imported store/day missingness is now available on the isolated dashboard using existing scoped SQL. It is a snapshot ending at the latest authorized record, not a live feed or proof of complete data. No M20 assembly occurred.
