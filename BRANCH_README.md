# Branch README

Branch: platform/agentic-rag
Parent branch / base commit: foundation/core-platform / 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045
Milestone: M11 PASS; official completion 23% (M0 5% + M1 10% + M11 8%)
Owner scope: ingestion, chunking, embeddings, ChromaDB, retrieval, verification and RAG tests
Human approval status: user authorized continuation; no cross-branch integration or main merge approved

## Purpose
Provide an isolated local Agentic RAG baseline using ChromaDB and sentence-transformers. Inherited master/governance documents are M0 snapshots; this branch delta records M11 implementation.

## Source-defined responsibilities
Document ingestion, canonicalization/chunking, provenance metadata, local embeddings, vector storage, top-k retrieval, relevance checks, bounded retrieve/reason/verify/re-retrieve, source evidence and integrity hooks. Reasoning here is deterministic evidence coverage and extractive assembly, not an LLM call.

## Allowed file scope
app/rag/*, tests/rag/*, branch README/checklist and branch graph delta. No SHARED DELTA. Foundation source/config/requirements and all other branches remain unchanged.

## Interfaces consumed
Foundation Contract for strict Pydantic validation. No agent implementation is consumed or integrated.

## Interfaces produced
- Document: explicit ID, immutable version, source, domain, access tag, fixture label and text; maximum 200,000 characters.
- RagSettings: chunk size/overlap, top-k, maximum iterations, cosine threshold and query-coverage threshold.
- chunk_document: Unicode NFC/whitespace canonicalization, overlapping word chunks, stable IDs, whole-document and content/provenance hashes.
- LocalSentenceTransformer: CPU model loaded from a local directory, remote code disabled and local_files_only=True. encode normalizes vectors. Caller supplies a pinned identity; collection rejects different identities.
- ChromaStore: persistent local collection, explicit vectors, cosine distance, scoped query filters, immutable revision checks and idempotent upsert. Use one ingestion writer; concurrent writers are not supported by the revision check. Maximum 1,000 chunks in a batch.
- RagPipeline.query: trusted access tag/domain, top-k retrieval, hash verification before evidence use, similarity/lexical relevance, missing-concept query rewrite, bounded iterations and conservative final evidence coverage check.
- RagResult: evidence_found, insufficient_evidence or knowledge_base_empty; quotes with numbered source metadata, iterations, metadata-only trace, and fixture/integrity warnings.

## Deliverables
Persistent Chroma store, local embedding adapter, canonical ingestion, typed results, bounded pipeline, scope guard, offline fixture demo and 13 RAG tests.

## Dependencies and decisions
Branch-local app/rag/requirements.txt adds ChromaDB (required vector persistence/filter/query engine) and sentence-transformers (required local embeddings). Foundation has no equivalents. Both are tested with real implementations. sentence-transformers pulls PyTorch; install a CPU build first on a student machine to avoid unnecessary CUDA downloads. No cloud credentials, paid service or model download is needed for the fixture tests. Dependencies are constrained, not a reproducible production lockfile.

## Setup and demo
From this repository root in your activated Python 3.11+ virtual environment (tested with Python 3.12):

```bash
python -m pip install -r requirements-dev.txt
# CPU-only PyTorch can be installed before the RAG requirements:
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r app/rag/requirements.txt
python -m pytest -q
python -m app.rag.demo
python -m app.rag.check_scope
```

The demo creates a tiny sentence-transformers BoW + Normalize model and a Chroma directory in a temporary folder. Its refund policy is synthetic and explicitly labelled. No pretrained transformer or real policy is claimed. The measured fixture retrieval tests establish wiring and failure handling, not production semantic accuracy.

To use real locally provisioned embeddings and text:

```python
from pathlib import Path
from app.rag.contracts import Document, RagSettings
from app.rag.embeddings import LocalSentenceTransformer
from app.rag.ingestion import chunk_document
from app.rag.store import ChromaStore
from app.rag.pipeline import RagPipeline

# Provision a vetted model separately and pin its identity to its revision.
embedder = LocalSentenceTransformer('/absolute/path/to/model', 'model-name@revision')
# Keep private vector databases outside this repository.
store = ChromaStore(Path('/absolute/private/path/retailops-chroma'), embedder)
settings = RagSettings()
# trusted_text is text extracted from an approved local document.
document = Document(document_id='policy-001', version='v1', source='approved-policy.txt',
                    domain='support', access_tag='support-team', text=trusted_text)
store.add(chunk_document(document, settings))
# Scope must come from a trusted authorization adapter, never untrusted request input.
result = RagPipeline(store, settings).query('What is the refund policy?',
                                          access_tag='support-team', domain='support')
```

## Tests
`python -m pytest -q`: 33 passed, 0 failed, 0 skipped (20 foundation + 13 RAG). Two inherited Starlette/AnyIO deprecation warnings. Test cases: persistence/reopen, source evidence, empty store, invalid query, access filtering, insufficient evidence, iteration bound, missing-concept rewrite, top-k ranking, tampered text/provenance, immutable revisions (including shortened documents), chunk overlap, model identity mismatch and missing local models. Demo completed with evidence_found and explicit fixture warning.

## Knowledge graph changes
Branch JSON maps RAG files/imports/contracts, pipeline stages, test relationships and dependencies. Master graph remains unchanged. No other branch metadata updated.

## Data dependencies
No real policy documents, SOPs, dataset or pretrained model weights supplied. Tests use a local lexical sentence-transformers model. Pretrained semantic model quality remains unevaluated. The ingestion boundary accepts text, not a PDF/OCR/Word parser.

## Known limitations
Coverage/similarity are heuristics, not factual entailment or answer confidence. This version quotes evidence rather than generating prose. No LLM reasoning/provider integration, LangGraph orchestration or FastAPI route registration is included. Multiple explicit document versions coexist; latest-version selection/retention is not implemented. Revision conflict protection assumes one ingestion writer. Thresholds need a labelled retail evaluation set. Persisted vectors inherit document sensitivity. No production accuracy claim.

## Cross-branch dependencies
Domain agents will consume these contracts after explicit integration approval. Security branch must provide authenticated scope mapping, trusted digest storage, stronger authorization and audit integrity. No branch was merged, rebased or cherry-picked.

## Security considerations
Filters run inside vector queries before returned text is processed, but caller-provided access_tag is a trusted internal input, not authentication. Unkeyed SHA-256 detects mismatches only; an attacker who rewrites content and hashes can evade it. Metadata/provenance are included in the hash. Embedding identity is caller-pinned, not a cryptographic verification of model weights. Retrieved content is quoted data; no tool calls or model instruction execution occurs. Full prompt-injection/RBAC protection is not claimed. Chroma anonymized telemetry is disabled. No credentials/private data committed.

## Last validated commit
Pinned foundation base 77c8c9217fa45d9028fbe8ad1fb22c4ea53e3045. The published implementation SHA and final remote SHA are recorded at the savepoint.

## Latest test result
33 passed; demo passed. Compile, dependencies, graph and scope validated before publication. Implementation savepoint c31c4e077f7a3e45a19181d6dc2df6fb8cba0837 published and verified with git ls-remote. Main, context and foundation remain unchanged. Official completion 23%.

## Next tasks
Verify M11 publication; create agent/router from pinned foundation, implement intent plans and escalation on that branch; implement inventory on its own branch; evaluate pretrained embeddings against real approved retail documents. Integration remains a separate human gate.
