# M20 integration plan - NOT AUTHORIZED / NOT EXECUTED

Do not create or merge the integration candidate until the human approves exact source commits and the base. Main and integration/dual-model-retailops remain protected. This plan is not an approval request during the unattended window and is not evidence of acceptance.

Proposed base: integration/dual-model-retailops@c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. Proposed candidate name: integration/ml-realtime-candidate.

## Exact source checkpoints

| Branch | Commit |
|---|---|
| docs/ml-methodology | e8f8280caa98d4a8f1bb504b64bc864699c9e7ed |
| platform/ml-core | ca22a9f755504de656093eba1f026c6aee620efa |
| platform/realtime-data | c944c3edb03eb98fcbb451096a47bb5d5bbc34f9 |
| ml/forecasting-models | 7ad9a4adaeccd18da383502739aa7a9020fc9381 |
| ml/auxiliary-models | 4a26af9b20958f7d4f160979ceb94f23067ed0d2 |
| ui/ml-dashboard | b20323252a68e6da3b82f95396783b231ac6b43b |

## Assembly and verification after approval

1. Recheck clean working tree, remote refs, dependencies and approval scope. Preserve unrelated local files. Create candidate from the approved base; never use main as a workspace.
2. Bring in methodology, ML core and real-time source checkpoints. Forecasting already descends from ML core; do not duplicate or overwrite that dependency. Auxiliary and dashboard descend independently from the showcase base. Resolve branch-record overlaps by archiving source records and writing a new integration record; do not lose inherited acceptance evidence.
3. Compose explicit mount hooks in one candidate launcher. Keep the standard terminal token behavior. Bind local-only by default. Keep all current authentication, store scope, audit and baseline fallback paths.
4. Replace offline dashboard evidence loading only with a documented scoped service contract; preserve the frozen benchmark display separately from live predictions. Integrate M16 freshness and SSE only after route and store-scope tests. Historical ERA5 data cannot be used as if it were an archived forecast.
5. Do not promote M17 candidates automatically. Delivery candidates failed the Brier comparison; keep descriptive delivery reporting. Use model/registry versions and baseline fallback explicitly. Models must never execute pricing, hiring, inventory or other business actions.
6. Run full regression, source-preservation checks, role/store API isolation, expired/revoked-token and reconnect checks, corrupt/missing artifact behavior, offline/weather-failure fallback, freshness and bounded stream checks. Complete desktop and mobile browser acceptance, keyboard and reduced-motion checks.
7. Publish an exact-commit validation report and source manifest, then seek separate approval for any release action. No main merge or production deployment is implied.

## Unresolved acceptance gaps

M17: global pooled boosting, measured quantile/feature-importance comparison, forecast-vintage weather/festival ablation, real benchmark and independent review. The synthetic test is already opened: future tuning cannot claim independence by reusing it. Calibration undercoverage must remain visible.

M18: human-reviewed router labels, expanded RAG benchmark, seasonal anomaly comparison, similarity ranking relevance, price-effect uncertainty and genuine stock/lead-time labels. Current metrics are synthetic, descriptive or injected proxies only.

M19: actual live panels, missingness/importance views and mobile browser acceptance. Current separate launcher serves /ml at port 8002 and does not modify the default website.

These are partial checkpoints, not M17-M20 completion. No real-world accuracy or universal acceptance claim is justified.

Latest supplemental development measurements and draft router/retrieval diagnostics do not satisfy independent accuracy or human-review gates. The new importance panel still requires browser verification.
