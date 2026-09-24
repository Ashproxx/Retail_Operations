# RetailOps AI

Privacy-first retail operations backend with a LangGraph router, eight domain agents, local Chroma retrieval, and authenticated FastAPI endpoints. This is the human-approved `integration/release-candidate`; it is not deployed and is not merged into `main`.

**Status: M0-M12 PASS (95% weighted milestones); M13 INCOMPLETE pending real-data validation.** The integrated code, all 178 tests, Docker build/runtime/restart, real local Ollama inference and pinned pretrained retrieval checks pass. Measurements use labelled synthetic data; no real retail dataset was supplied, so operational business outputs and dataset-specific mappings are unverified. The percentage measures the project checklist, not production readiness. See [validation evidence](docs/integration/VALIDATION.md).


## Start locally (Python 3.12)

```bash
git clone --branch integration/release-candidate https://github.com/Ashproxx/Retail_Operations.git
cd Retail_Operations
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in Windows PowerShell, or `source .venv/bin/activate` in bash. Then:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-dev.txt
python -m app.integration.cli init
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Open `http://127.0.0.1:8000/docs` and `/health`. Startup creates empty tables; it never loads demo inventory. `init` generates a random local admin token in `secrets/admin-token.txt`, its SHA-256 grant in `secrets/grants.json`, and configuration in `.env`. These are ignored by git and excluded from Docker builds. Do not upload them. For PowerShell, load the token into memory with `$token = (Get-Content secrets/admin-token.txt -Raw).Trim()` and send `Authorization: Bearer $token`. Tokens are opaque random secrets, not passwords. Provision separate grants with role, store IDs and optional timezone-aware `expires_at`; revoke by removing the grant and restarting.

Without a grants file the default runtime denies all authenticated API calls. An explicitly configured missing/malformed grants file fails startup. API payloads cannot claim a role or principal. All date-only defaults use the current UTC day and are disclosed in results. Order queries require a timezone-aware timestamp when supplied.

## APIs

| Endpoint | Purpose |
|---|---|
| `GET /`, `GET /health` | Public service and database health |
| `POST /api/chat` | Conservative English routing, execution, aggregation and follow-ups |
| `POST /api/query` | Explicit registered agent ID and typed parameters |
| `POST /api/forecast` | Forecast parameters (same envelope as chat) |
| `GET /api/inventory/low-stock`, `/api/inventory/{store_id}` | Authorized inventory results |
| `GET /api/analytics/summary` | Authorized sales/KPI output |
| `POST /api/rag/ingest` | Administrator-only document ingestion |
| `POST /api/rag/query` | Scoped, signature-verified retrieval |
| `GET /api/audit` | Administrator-only verified chain and anchor |
| `POST /api/feedback` | Feedback for a request owned by this principal/session |

Every `/api` call requires a bearer token. `/health` checks the database, not model quality or downstream connector readiness. Validation/authentication/infrastructure errors use 422/401/403/503 (unexpected failures use sanitized 500). Chat/query return a structured 200 response with `data.status`, `requires_human`, and per-agent statuses for clarification, insufficient data, denied operations and domain failures. Never interpret HTTP 200 alone as successful business execution.

Chat JSON (using actual store/SKU identifiers from your imports):

```json
{"message":"Inventory is low but demand is increasing. What actions should be considered?","session_id":"demo-001","parameters":{"store_id":"BANDRA","sku_id":"SHIRT-1","as_of":"2026-09-22"}}
```

The identifiers/date above refer to synthetic demo fixtures; they are not preloaded. On empty data the service returns missing/insufficient evidence. For a low-stock session, `Which products are low in Bandra?` followed by `What about Andheri?` retains the low-stock action and changes the recognized store. Session state stores intent/parameters for 24 hours, keyed by principal and session; authorization is repeated on every call. Free-form conversation memory and broad semantic language understanding are not claimed.

Structured JSON:

```json
{"agent":"inventory","session_id":"demo-001","parameters":{"action":"low_stock","store_id":"BANDRA","as_of":"2026-09-22"}}
```

Supported IDs: `inventory`, `demand-forecasting`, `analytics-reporting`, `pricing-promotions`, `supply-chain`, `order-fulfillment`, `customer-service`, `returns-refunds`. Inspect exact input contracts with `python -m app.integration.cli schema --agent inventory`. Forecasts require store/SKU, orders and returns require store/order; missing IDs are not guessed. Analytics without dates reports the range of available observations. Historical/relative dates outside the supported aliases require explicit parameters.

## Import CSV or XLSX

No real dataset was supplied. The integration stores each domain's Pydantic-validated observed record in a SQLAlchemy JSON payload with indexed agent/store identity. This avoids inventing unavailable production schemas. `stores` holds recognized IDs/names; normalized operational product/order tables and migrations remain future work when a real schema is supplied. `session_state`, `request_receipts`, and `signed_rag_manifest` support the shared services. `Repository.records` authorizes before issuing its structured SQL query. No LLM generates SQL.

Create a source-column to contract-field JSON map, for example:

```json
{"store_id":"store_id","sku_id":"sku_id","date":"observed_on","closing_stock":"closing_stock","reorder_point":"reorder_point","vendor_lead_time_days":"lead_days"}
```

```bash
python -m app.integration.cli load --agent inventory --file your_inventory.csv --mapping inventory-map.json
```

Use `--stores stores.json` to supply an ID/name map such as `{"BANDRA":"Bandra"}`; otherwise IDs are their own names. Use `--fixture` only for synthetic development data. `source` and `fixture` are assigned by the importer. Blank required values, invalid dates, negative stock, duplicate headers/identities and formula cells are rejected; the entire batch rolls back. XLSX reads the active sheet. Limits: 20 MB input, 10,000 rows, 100 XLSX columns. Nested domain values use JSON cells. Existing observations are immutable: a duplicate is an error, not an upsert. No path-upload HTTP endpoint exists; importing is a trusted local operator command.

Different agents have deliberately different record contracts. Map the same real daily-sales file separately into `analytics-reporting` and `demand-forecasting` (e.g. `units_sold` -> `units` for forecasting). Do not assume inventory implies sales, prices, vendors, orders or returns.

## Local RAG

Set these server-owned values in `.env`:

- `RETAILOPS_EMBEDDING_MODEL_PATH`: existing local sentence-transformers model directory.
- `RETAILOPS_EMBEDDING_IDENTITY`: pinned model/revision identifier; changing models requires a new Chroma collection/state location.
- `RETAILOPS_INTEGRITY_KEY`: at least 32 bytes; generated by `init`. Back it up privately. Rotation requires deliberate re-signing/re-ingestion.
- `RETAILOPS_MAX_RAG_ITERATIONS`: default 3, maximum 10.

Models are loaded locally with remote code disabled. No automatic model download occurs. An absent configuration returns 503 for explicit RAG queries; support still uses any available approved local policies and reports the unavailable RAG component. Development only: `python -m app.integration.cli fixture-model` creates a local BoW sentence-transformers model; set the path to `models/fixture-bow` and identity to `fixture-bow-v1`. This tests plumbing, not pretrained semantic relevance. Label documents as fixtures when using synthetic content.

Administrator ingestion payload:

```json
{"session_id":"ingestion","document":{"document_id":"fixture-hours","version":"1","source":"fixture://hours","domain":"support","access_tag":"BANDRA","text":"Customer service FAQ opening hours are nine to five.","fixture":true}}
```

Query payload:

```json
{"session_id":"demo-001","question":"opening hours","store_id":"BANDRA","domain":"support"}
```

`access_tag` is the exact store ID. Domains: inventory, forecasting, analytics, pricing, orders, supply, support, returns. Role/scope authorization precedes retrieval. A SQL-stored HMAC-SHA256 manifest binds all chunk content/provenance fields; Chroma's own hash alone is insufficient. Recomputed hashes without a valid signature are rejected. A crash between vector insertion and manifest commit leaves unsigned chunks unusable. Retrieval is bounded and extractive; query-coverage scores are heuristics. Multiple relevant support documents conservatively escalate for review. RAG excerpts do not assert policy approval or validity dates. Evidence never executes tools.

## Local LLM and later hosting

`RETAILOPS_LLM_PROVIDER=ollama`, `RETAILOPS_OLLAMA_URL=http://localhost:11434`, and `RETAILOPS_OLLAMA_MODEL=<installed model>` configure the local `/api/chat` provider. `draft_with_llm: true` requests a separate `unverified_llm_draft` after successful deterministic execution. It cannot overwrite facts or remove escalation. Failure leaves deterministic results available. Set `RETAILOPS_LLM_PROVIDER=deterministic` for offline testing. The `Provider` protocol is the Azure/OpenAI extension point; hosted adapters are not implemented and there is no automatic external fallback. Azure deployment remains later work.

## Tests and demo

```bash
python -m pytest -q
python -m pip check
python scripts/check_branch_scope.py
python -m app.integration.demo
```

The demo uses a temporary database, random ephemeral credentials and explicitly synthetic records. It does not modify your database. Tests cover all isolated agent suites plus authenticated API execution, follow-ups, role/store denials, feedback ownership, atomic CSV/XLSX imports, Ollama protocol/failure via mocked transport, actual Chroma/local-model retrieval, and signed-manifest tampering. The unit suite alone does not establish live-model behavior. Separate executed validation scripts verify real Ollama transport/inference and pretrained retrieval on the small synthetic set; neither establishes production answer quality.

## Docker and CI

After local `init`, run `docker compose up --build`. Place an approved local embedding model at `models/embedding` and set its identity in `.env` for RAG. The container exposes port 8000 only on localhost, uses a non-root user, read-only secret/model mounts, a persistent state volume, CPU PyTorch and one worker. On Linux, files generated with mode 0600 must be readable by container UID 10001 through an appropriate owner/group or secret provisioning setup; do not make tokens world-readable. Ollama runs on the host; ensure its local server is reachable from Docker before using optional drafting. No cloud resources are created.

GitHub Actions installs CPU dependencies, runs the full suite, demo, scope guard and Docker build on candidate pushes/PRs with read-only repository permissions. [Expanded CI run 35909119561](https://github.com/Ashproxx/Retail_Operations/actions/runs/35909119561) passed all 178 tests, Docker build, real local-model inference and non-root authenticated container/restart workflows. Measured reports are recorded in docs/integration/VALIDATION.md.

## Limits and trust boundaries

- English routing and parameter extraction are conservative rules; missing/ambiguous inputs request clarification. Confidence is uncalibrated and results expose assumptions.
- No production price changes, purchase orders, refunds, shipments, support tickets or notifications are executed.
- Game-theory/Bayesian/elasticity/fraud extensions remain interfaces or limited labelled simulations as documented in source archives.
- Local audit logs use a single writer. Run one process/worker. Keep anchors independently to detect deletion/full rewrite across restarts; hash chaining alone cannot protect against an attacker controlling both log and anchor. Audit growth/rotation and retention need operational policy.
- Protect the SQL database, filesystem grants, key, session state and feedback. HMAC does not protect against compromise of the signing service. Revocation takes effect after reloading grants/restarting.
- No public internet deployment, TLS termination, rate limiting, enterprise identity, production connectors or operational dataset validation is claimed.

See [ARCHITECTURE.md](ARCHITECTURE.md), [integration report](docs/integration/REPORT.md), [approved source commits](docs/integration/APPROVED_SOURCES.json), and [knowledge graph](docs/knowledge_graph/MASTER_KNOWLEDGE_GRAPH.md). Every original branch README/checklist/graph is preserved under `docs/integration/sources/`.

## Extended validation

The candidate includes explicit development evaluation commands. These download public model weights only when you run the download command; application startup still makes no model downloads. All model inputs below are synthetic. Models and revisions are recorded in `evaluation/models.json`: Apache-2.0 MiniLM-L6-v2 at a pinned commit for embeddings, and SmolLM2 135M through Ollama for a small CPU inference smoke test. No paid service is required.

```bash
python -m scripts.download_evaluation_model --output models/evaluation-minilm
python -m scripts.evaluate_retrieval --model-path models/evaluation-minilm --output validation-output/retrieval.json
python -m scripts.live_ollama_smoke --output validation-output/ollama.json
python -m scripts.container_smoke --with-ollama --output validation-output/container.json
```

The last two commands need Ollama listening on port 11434 with `smollm2:135m` installed; the container command additionally needs the built `retailops-candidate` image and Docker. CI provisions both services and archives only non-secret measured reports. Retrieval uses 12 authored positive queries, six synthetic documents and two negative questions. Thresholds are development regression gates, not production accuracy certification. Container validation checks UID 10001, missing-token rejection, empty-database behavior, authorized query, denied store access, real-model draft, persistence across restart and owned feedback. Generated drafts are bounded to 256 tokens and remain separate from deterministic facts.
