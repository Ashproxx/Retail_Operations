from typing import Literal
from pydantic import Field, model_validator
from app.api.schemas import Contract


class RagSettings(Contract):
    chunk_words: int = Field(default=160, ge=8, le=1000)
    overlap_words: int = Field(default=24, ge=0)
    top_k: int = Field(default=4, ge=1, le=50)
    max_iterations: int = Field(default=3, ge=1, le=10)
    min_similarity: float = Field(default=0.35, ge=0, le=1)
    min_query_coverage: float = Field(default=0.5, gt=0, le=1)

    @model_validator(mode="after")
    def valid_overlap(self):
        if self.overlap_words >= self.chunk_words:
            raise ValueError("Overlap must be smaller than chunk size")
        return self


class Document(Contract):
    document_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    access_tag: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=200000)
    fixture: bool = False


class Chunk(Contract):
    chunk_id: str
    document_id: str
    version: str
    source: str
    domain: str
    access_tag: str
    text: str
    fixture: bool
    content_hash: str
    document_hash: str


class Hit(Contract):
    chunk: Chunk
    similarity: float = Field(ge=0, le=1)


class RagResult(Contract):
    status: Literal["evidence_found", "insufficient_evidence", "knowledge_base_empty"]
    answer: str
    sources: list[Hit] = Field(default_factory=list)
    iterations: int = Field(ge=0)
    trace: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
