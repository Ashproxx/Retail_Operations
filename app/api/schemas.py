"""Shared contracts. A client-supplied role is never authorization."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Role(str, Enum):
    ADMIN = "ADMIN"
    STORE_MANAGER = "STORE_MANAGER"
    INVENTORY_MANAGER = "INVENTORY_MANAGER"
    PRICING_ANALYST = "PRICING_ANALYST"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ANALYST = "ANALYST"


class QueryRequest(Contract):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(min_length=1, max_length=128)


class RequestContext(Contract):
    """Internal only: constructed by a future trusted authentication adapter."""
    request_id: UUID = Field(default_factory=uuid4)
    session_id: str = Field(min_length=1, max_length=128)
    principal_id: str = Field(min_length=1)
    role: Role
    store_ids: list[str] = Field(default_factory=list)


class Evidence(Contract):
    document_id: str
    source: str
    chunk_id: str | None = None
    content_hash: str | None = None


class AgentResult(Contract):
    agent: str = Field(min_length=1)
    request_id: UUID
    status: Literal["success", "not_found", "insufficient_evidence", "error", "escalated"]
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    recommended_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    requires_other_agents: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    latency_ms: float = Field(default=0, ge=0)


class ChatResponse(Contract):
    session_id: str
    agents_used: list[str]
    answer: str
    data: dict[str, Any] = Field(default_factory=dict)
    sources: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class AuditEvent(Contract):
    request_id: UUID
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_role: Role
    router_decision: list[str] = Field(default_factory=list)
    agents_called: list[str] = Field(default_factory=list)
    tools_called: list[str] = Field(default_factory=list)
    documents_retrieved: list[str] = Field(default_factory=list)
    rag_iterations: int = Field(default=0, ge=0)
    confidence: float = Field(ge=0, le=1)
    latency_ms: float = Field(ge=0)
    final_status: str


class ErrorResponse(Contract):
    code: str
    message: str
    request_id: UUID
