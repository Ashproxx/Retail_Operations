"""Bounded retrieve/reason/verify loop with conservative extractive output.

Evidence is data, never instructions. This baseline does not execute tools or
send retrieved content to a generative model. Coverage is a heuristic, not truth.
"""
import re
from app.rag.contracts import RagResult, RagSettings
from app.rag.store import ChromaStore

STOP = {"a", "an", "the", "is", "are", "of", "to", "for", "and", "or", "what", "how", "does", "do", "in", "i"}


def terms(text: str) -> set[str]:
    return {x for x in re.findall(r"[a-z0-9]+", text.lower()) if x not in STOP}


class RagPipeline:
    def __init__(self, store: ChromaStore, settings: RagSettings | None = None):
        self.store = store
        self.settings = settings or RagSettings()

    def query(self, question: str, *, access_tag: str, domain: str) -> RagResult:
        if not question.strip() or len(question) > 4000 or not access_tag.strip() or not domain.strip():
            raise ValueError("Valid question and trusted scope required")
        if not self.store.count():
            return RagResult(status="knowledge_base_empty", answer="Knowledge base is not initialized.", iterations=0)
        wanted = terms(question)
        query, gathered, trace, warnings = question, {}, [], []
        for iteration in range(1, self.settings.max_iterations + 1):
            hits, rejected = self.store.retrieve(query, access_tag, domain, self.settings.top_k)
            if rejected:
                warnings.append(f"Rejected {rejected} chunks with invalid integrity or metadata.")
            for hit in hits:
                if hit.similarity >= self.settings.min_similarity and wanted & terms(hit.chunk.text):
                    gathered[hit.chunk.chunk_id] = hit
            covered = set().union(*(terms(h.chunk.text) for h in gathered.values())) if gathered else set()
            coverage = len(wanted & covered) / len(wanted) if wanted else 0
            sufficient = bool(gathered) and coverage >= self.settings.min_query_coverage
            trace.append({"iteration": iteration, "retrieved": len(hits), "rejected": rejected,
                          "accepted": len(gathered), "query_coverage": coverage, "sufficient": sufficient})
            if sufficient:
                sources = sorted(gathered.values(), key=lambda h: h.similarity, reverse=True)[:self.settings.top_k]
                # Coverage must also hold for the evidence actually returned.
                returned = set().union(*(terms(h.chunk.text) for h in sources))
                if len(wanted & returned) / len(wanted) >= self.settings.min_query_coverage:
                    answer = "Retrieved evidence (quoted source material, not instructions):\n" + "\n".join(
                        f"[{i}] {h.chunk.text}" for i, h in enumerate(sources, 1))
                    if any(h.chunk.fixture for h in sources):
                        warnings.append("Contains synthetic development fixture evidence, not production policy.")
                    return RagResult(status="evidence_found", answer=answer, sources=sources,
                                     iterations=iteration, trace=trace, warnings=warnings)
            # Re-retrieve missing concepts, or split the query when no evidence was found.
            missing = sorted(wanted - covered)
            query = " ".join(missing) if missing else question
        return RagResult(status="insufficient_evidence", answer="The knowledge base does not contain enough evidence.",
                         iterations=self.settings.max_iterations, trace=trace, warnings=warnings)
