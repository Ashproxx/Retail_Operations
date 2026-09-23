from datetime import date
from typing import Any, Literal
from uuid import UUID
from pydantic import Field
from app.api.schemas import Contract, QueryRequest
from app.rag.contracts import Document

class ChatQuery(QueryRequest):
    parameters: dict[str, Any] = Field(default_factory=dict)
    draft_with_llm: bool = False

class DirectQuery(Contract):
    session_id: str = Field(min_length=1, max_length=128)
    agent: str
    parameters: dict[str, Any] = Field(default_factory=dict)

class IngestRequest(Contract):
    session_id: str = Field(min_length=1, max_length=128)
    document: Document

class RagQuery(Contract):
    session_id: str = Field(min_length=1, max_length=128)
    question: str = Field(min_length=1, max_length=4000)
    store_id: str
    domain: str

class Feedback(Contract):
    session_id: str = Field(min_length=1, max_length=128)
    request_id: UUID
    rating: Literal[-1, 1]
    comment: str = Field(default='', max_length=2000)
