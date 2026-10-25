# Expanded retrieval development evaluation

Freeze fixture and evaluator before running. The fixture has 50 positive queries (five per policy document) and 15 unanswerable queries, including near-domain questions whose requested fact is absent. All ten policy documents are fictional. Labels are agent-authored and NOT human-reviewed. No production policy is inferred.

Fit TF-IDF unigrams/bigrams on the ten authorized documents only. Queries do not fit vocabulary or IDF. Use the existing ChromaStore, SignedRag, VerifiedStore and RagPipeline without changing production code or settings. No semantic model is downloaded. Insert a query-rich forbidden-store document to test isolation; it is excluded from vectorizer fitting and must never appear in retrieved or returned evidence.

Measure Recall@1/3, MRR@3, nDCG@3 for a single relevant document per positive, plus negative abstention rate, abstention precision across both positive and negative cases, and positive evidence rate. Preserve all failures. No tuning/relabeling after evaluation. This is a lexical baseline and integration check, not a generalization claim or human acceptance gate. Evidence-found is not entailment or answer correctness.

Run `python -m scripts.evaluate_auxiliary_rag`; output is docs/auxiliary/RAG_RESULTS.json and refuses overwrite. SQLite and Chroma are temporary; no source workbook, employee record, model weights or external service is used. Added scope: app/auxiliary/retrieval.py, scripts/evaluate_auxiliary_rag.py, tests/auxiliary/test_retrieval.py and auxiliary documentation/fixture.
