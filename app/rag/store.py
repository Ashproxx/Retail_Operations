"""Persistent Chroma vector store; explicit embeddings and scoped retrieval."""
import math
from pathlib import Path
import chromadb
from chromadb.config import Settings
from app.rag.contracts import Chunk, Hit
from app.rag.embeddings import Embedder
from app.rag.ingestion import verify


class ChromaStore:
    def __init__(self, path: Path, embedder: Embedder, collection: str = "retailops-evidence"):
        self.embedder = embedder
        self.client = chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(
            collection, embedding_function=None,
            metadata={"embedding_identity": embedder.identity},
            configuration={"hnsw": {"space": "cosine"}})
        if (self.collection.metadata or {}).get("embedding_identity") != embedder.identity:
            raise ValueError("Embedding identity differs; use a new collection")

    def count(self) -> int:
        return self.collection.count()

    def add(self, chunks: list[Chunk]) -> int:
        if not chunks:
            raise ValueError("No chunks to ingest")
        if len(chunks) > 1000:
            raise ValueError("Ingest at most 1000 chunks per document batch")
        if not all(verify(c) for c in chunks):
            raise ValueError("Invalid chunk digest")
        ids = [c.chunk_id for c in chunks]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate chunk IDs")
        existing = self.collection.get(ids=ids, include=["metadatas"])
        old = dict(zip(existing["ids"], existing["metadatas"]))
        for chunk in chunks:
            if chunk.chunk_id in old and old[chunk.chunk_id]["content_hash"] != chunk.content_hash:
                raise ValueError("Document revision already exists with different content; use a new version")
        vectors = self.embedder.encode([c.text for c in chunks])
        self.collection.upsert(ids=ids, embeddings=vectors, documents=[c.text for c in chunks],
                               metadatas=[c.model_dump(exclude={"text", "chunk_id"}) for c in chunks])
        return len(chunks)

    def retrieve(self, query: str, access_tag: str, domain: str, top_k: int) -> tuple[list[Hit], int]:
        if not query.strip() or not access_tag.strip() or not domain.strip() or not 1 <= top_k <= 50:
            raise ValueError("Query, trusted access scope, domain and valid top_k required")
        if not self.count():
            return [], 0
        result = self.collection.query(query_embeddings=self.embedder.encode([query]), n_results=top_k,
            where={"$and": [{"access_tag": access_tag}, {"domain": domain}]},
            include=["documents", "metadatas", "distances"])
        hits, rejected = [], 0
        for id, text, meta, distance in zip(result["ids"][0], result["documents"][0],
                                          result["metadatas"][0], result["distances"][0]):
            try:
                chunk = Chunk(chunk_id=id, text=text, **meta)
                if not verify(chunk) or not math.isfinite(distance):
                    raise ValueError("Invalid evidence")
                hits.append(Hit(chunk=chunk, similarity=max(0, min(1, 1-distance))))
            except (ValueError, TypeError):
                rejected += 1
        return hits, rejected
