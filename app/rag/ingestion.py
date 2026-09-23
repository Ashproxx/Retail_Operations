"""Canonical immutable chunks; bind provenance to the content digest."""
import hashlib
import json
import unicodedata
from app.rag.contracts import Chunk, Document, RagSettings


def clean(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def verify(chunk: Chunk) -> bool:
    return digest(chunk.model_dump(exclude={"content_hash"})) == chunk.content_hash


def chunk_document(document: Document, settings: RagSettings) -> list[Chunk]:
    words = clean(document.text).split()
    if not words:
        raise ValueError("Document contains no text")
    identity = digest(document.model_dump(exclude={"text"}))
    result = []
    for start in range(0, len(words), settings.chunk_words - settings.overlap_words):
        payload = document.model_dump(exclude={"text"})
        payload.update(document_hash=digest({"text": clean(document.text)}), chunk_id=f"{identity}:{start}", text=" ".join(words[start:start+settings.chunk_words]))
        result.append(Chunk(**payload, content_hash=digest(payload)))
        if start + settings.chunk_words >= len(words):
            break
    return result
