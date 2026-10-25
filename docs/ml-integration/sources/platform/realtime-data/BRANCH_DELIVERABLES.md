# M16 real-time data branch

Branch: platform/realtime-data. Base: integration/dual-model-retailops@c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. User authorized the four areas, restricted work to branches, and approved suitable educational weather calls after terms review.

Owned: app/realtime, scripts/backfill_weather.py, tests/realtime, docs/realtime, and documented .env.example settings. No normal app startup change; composition is explicit via app.realtime.launch/install. Only isolated candidate DB was used. Existing integration/main refs and historical source code remain unchanged.

Delivered: approved weather connector and ERA5 backfill (8,784/8,784 hours), seeded synthetic stream, validated append-only deduplication, signed webhook, scoped SSE, freshness and online features, explicit one-worker lifespan, offline tests and live smoke. Detailed setup, attribution and safety limits: docs/realtime/RUNBOOK.md. M19 UI and M20 integration are still separate work; no accuracy or full milestone completion is claimed.

No dependency added. Configuration uses existing pydantic-settings/httpx/SQLAlchemy. Branch guard shared delta remains solely on platform/ml-core; no cross-branch copy occurred. Graph is a branch-local delta. Integration requires human approval.

---

## Historical inherited record

# Integration deliverables

Current Phase 3 deliverables: [development report](docs/phase3/VALIDATION.md) and [hard milestone ledger](docs/phase3/MILESTONES.md). Source SQL importers, separate retail/HR services, HR permissions, four-model selector and responsive website are implemented. Main merge requires explicit final authorization. Historical M13 below describes the earlier release only.

## Historical release candidate

M13 INCOMPLETE; weighted completion remains 95%.

- [x] Explicit approval recorded with pinned sources/base
- [x] Candidate created from approved foundation
- [x] Approved source commits integrated; source implementations preserved
- [x] Original metadata archived by branch
- [x] Authenticated API and explicit role/store checks before reads
- [x] All eight domain agents wired through LangGraph and registry
- [x] Multi-agent aggregation, conflict escalation and bounded execution
- [x] Conservative natural-language parameter bridge and scoped follow-up memory
- [x] Atomic CSV/XLSX ingestion with validation and fixture provenance
- [x] Persistent SQL records, owned feedback, durable audit chain
- [x] Real Chroma/local-embedding tests and signed-manifest rejection
- [x] Ollama protocol adapter and tested deterministic failure fallback
- [x] Full available automated suite and live Uvicorn startup verification
- [x] Docker and read-only CI configurations
- [x] Setup/API/data/architecture documentation and regenerated graphs
- [x] Source-preservation/ancestry scope guard
- [x] Candidate implementation pushed and fetched; file tree/ancestry verified
- [x] All fourteen pre-existing branch refs, including main, verified unchanged
- [x] Live Ollama smoke test with an installed model (SmolLM2 135M)
- [x] Pinned pretrained embeddings and labelled synthetic retrieval evaluation (MiniLM, 12 positive / 2 negative queries)
- [ ] Real retail dataset mapping and end-to-end validation
- [x] Previous remote CI and Docker image build verified (run 35878697558)
- [x] Expanded container runtime, real Ollama and pretrained retrieval checks verified (run 35909119561)
- [ ] M13 complete / eligible for final human review

Publication evidence and source/main ref checks are recorded in docs/integration/REPORT.md and the session report. No main merge is authorized.

## Interactive showcase extension

- [x] Responsive same-origin dashboard connected to authenticated inventory, analytics, forecast, chat, feedback and audit APIs.
- [x] Opt-in, localhost-only temporary synthetic database; normal operational startup remains empty.
- [x] Windows launch and presentation guide: [DASHBOARD.md](docs/integration/DASHBOARD.md).
- [x] Full local Python suite: 180 passed; source-preservation guard passed.
- [ ] Real dataset mapping and business validation (unchanged M13 requirement).
