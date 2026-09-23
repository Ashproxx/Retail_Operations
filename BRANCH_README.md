# Security branch README

Branch: security/privacy-integrity
Parent/base: foundation/core-platform / 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045
Milestone: M12 PASS
Official weighted completion: 95%
Owner scope: app/security/*, tests/security/* and branch metadata/graph delta
Human approval: continuation authorized; no M13 integration or main merge authorized

## Purpose and source-defined responsibilities
Role-based access before sensitive tools and retrieval; secret-safe configuration; document digest verification; standard keyed authentication of document/provenance metadata; structured metadata-only audit with hash-chain integrity. These branch-local controls still require integration into every operational route.

## Allowed file scope
app/security/*, tests/security/*, BRANCH_README.md, BRANCH_DELIVERABLES.md and branch knowledge graph Markdown/JSON. No shared delta. Foundation/global files and other branches remain unchanged.

## Interfaces consumed
Foundation Contract, Role, RequestContext, AuditEvent and RetailOpsError. No imports from other development branches.

## Interfaces produced
- Grant and TokenAuthenticator: opaque random bearer token grants stored as SHA-256 digests; optional expiration; creates context from server-owned principal/role/store mapping. No user role claims accepted. Provision random tokens (at least 32 bytes of entropy recommended) outside source control. This is a local opaque-token adapter, not a password authentication scheme or identity-provider integration.
- authorize(context, action, store_id): explicit action allowlist and role/store restrictions, deny by default. ADMIN can access all known actions; other roles require permitted action plus explicit store scope.
- ToolRegistry: trusted registrations, authorization before callbacks and rejection of reserved context overrides. User input cannot register callables.
- Document/SealedDocument, seal/verify: canonical JSON binds ID/version/store/domain/source/text with SHA-256 and standard HMAC-SHA256. Constant-time HMAC comparison uses Python hmac.compare_digest. Minimum key length 32 bytes; use a cryptographically random secret, not a human password.
- retrieve_verified: authorize before provider invocation, then validate every returned document's store/domain/digest/HMAC before releasing evidence. Provider must be a trusted configured adapter. No arbitrary tools or document instructions execute.
- AuditChain and verify_chain: sequenced JSONL metadata audit, SHA-256 linkage, fsync on append, restrictive mode for new files, optional trusted external anchor. The instance retains its latest anchor and detects deletion/truncation during its lifetime. Reopened logs need a separately trusted anchor to detect truncation or full rewrite.
- SecuritySettings: RETAILOPS_SECURITY_INTEGRITY_KEY from environment as SecretStr; no default secret and no credentials printed.

## Role/action matrix
| Role | Allowed actions |
|---|---|
| ADMIN | All known actions, including audit.read |
| STORE_MANAGER | All known operational actions; no audit.read |
| INVENTORY_MANAGER | inventory.read, forecast.read, supply.read |
| PRICING_ANALYST | pricing.recommend, forecast.read, analytics.read |
| SUPPORT_AGENT | orders.read, support.read, returns.read |
| ANALYST | analytics.read, forecast.read |

Non-admin access always requires an authorized store. Routing and request JSON do not confer authorization.

## Deliverables and tests
39 passed, 0 failed, 0 skipped: 20 foundation + 19 security cases. One inherited Starlette/httpx deprecation warning. Tests cover role matrix, unknown actions, out-of-scope stores, token mismatch/expiry, denial before tool/retrieval side effects, document/provenance tampering, wrong keys, source-scope mismatch, audit mutation/reordering/truncation/deletion, persisted anchors and secret-safe settings. Fixture demo generates keys in memory and never prints them.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m app.security.demo
python -m app.security.check_scope
python -m compileall -q app/security
```

Python 3.11+; validated on 3.12. No additional dependencies: standard hashlib/hmac/secrets/json plus foundation Pydantic suffice. Official primitive reference: https://docs.python.org/3/library/hmac.html .

## Knowledge graph changes
53 nodes and 69 relationships map ownership, imports, definitions and tests. Master graph remains inherited; only this branch delta changes. No cross-branch propagation.

## Data dependencies and security limitations
No real customer records, credentials or business data are included. Demo identities/policies are synthetic. Keys, token grants, audit logs and their anchors must be provisioned outside git. Existing file permissions, retention, key rotation, secret storage and deployment authentication are operator responsibilities. Static grant revocation requires replacing/reloading the authenticator; no external IdP or distributed policy engine is included.

Audit persistence assumes one writer per file/instance and a trusted filesystem. No multi-process lock is provided. Unanchored hashes cannot detect a complete attacker rewrite, and anchors saved alongside an attacker-writable log are not trusted. HMAC protects documents only while its secret key is protected. This does not encrypt data at rest. Retrieved text remains untrusted evidence; this branch does not send it to an LLM or execute instructions, and it does not claim to solve all prompt injection.

The authentication and authorization helpers are not yet wired into FastAPI or all other agent branches. Their presence alone does not make the full application production-secure.

## Cross-branch dependencies
Integration must connect authenticated context, registry actions and retrieval wrappers to every endpoint/agent and bridge RAG chunk metadata to signed document/provenance manifests. Domain modules currently expose structured JSON adapters; natural-language routing/execution and aggregation need wiring. No source branch was merged or copied into this branch.

## Last validated commit and latest result
Pinned base: 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045. Verified implementation savepoint: 15bdd6eb73f1564a950f167ca1f20fbea09f9f0f. Final remote documentation SHA is recorded in the session report. Tests, demo, compilation, scope and graph checks PASS. Publication verified.

## Human review and next tasks
M13 cannot begin until explicitly approved under PDF sections 2.3, 6.8 and 45. app/security/INTEGRATION_REVIEW.md lists the exact source commits and proposed candidate base. After approval, create integration/release-candidate, reconcile branch metadata and interfaces, complete shared integration requirements, and run full end-to-end verification. Main remains untouched and requires a separate merge instruction.
