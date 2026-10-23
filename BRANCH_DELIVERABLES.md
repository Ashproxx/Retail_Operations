# M19 model review dashboard - isolated candidate

Branch ui/ml-dashboard from c27fef0a0c5cf7c84551a5940ef3ced8e9f00b93. Scope: app/ml_dashboard, tests/ml_dashboard, scripts/export_ml_dashboard.py, docs/ml-dashboard and these records. Existing website and protected branches are untouched.

Candidate `/ml` shows frozen selected-before-test curves, 80% interval limits, measured 80%/95% coverage, metrics, comparison tables, exclusions and auxiliary status. Coffee/bronze styling, responsive layout, reduced-motion support and accessible table alternatives. Tokens remain in memory only. APIs authenticate and audit reads; managers/analysts see authorized stores only; global aggregate leaderboard and auxiliary evidence are ADMIN-only; HR roles denied. No client-supplied scope is trusted.

Reports are exported as local data from pinned commits: M17 primary 6b86795, supplement 7ad9a4a and M18 4a26af9. Source code is not merged. Checksums detect accidental report changes; this is not a signature against a malicious local administrator. Missing evidence fails closed. Independent launcher port 8002; normal server remains unchanged. Live feed honestly reports unavailable until M20 integration approval.

Remaining M19 scope: actual live freshness/stream wiring, missing-data and broader importance views and real benchmark comparisons cannot be demonstrated by the current evidence. M20 still needs exact-commit approval. No training, promotion or external transmission occurs in the dashboard.

---

## Inherited branch record

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

Checks: 5 dashboard tests; 219 full regression tests. Desktop browser verified; mobile acceptance pending. See docs/ml-dashboard/VALIDATION.md.

Chart correction: time axes preserve elapsed dates and null breaks prevent lines across unscored windows. Genuine zero values remain zero; missing values remain null. Node assert-based regression passed; 5 dashboard API tests passed. Browser verified h=7 separated windows and unchanged metrics. Screenshot: validation-output/ml-dashboard/dashboard-gaps.png. Full suite was not repeated for this isolated chart-only correction.


## Supplemental evidence panel

Admin-only feature-importance and quantile checks now read the pinned M17 supplement at 7ad9a4a. The panel explicitly labels the fourteen-day exploratory validation window and retains negative feature-importance values. Global chain evidence is omitted entirely from manager/analyst responses. Existing frozen test charts are unchanged. Re-run the local export script to add supplement.json; missing/corrupt evidence still fails closed.

Five dashboard API tests passed, including supplement suppression for scoped roles and ADMIN access. JavaScript syntax check passed. Visual browser acceptance of this added table remains pending; no new mobile acceptance is claimed. Real-time wiring still awaits M20 approval. No model is promoted.
