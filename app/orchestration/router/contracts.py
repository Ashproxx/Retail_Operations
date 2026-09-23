from enum import Enum
from pydantic import Field
from app.api.schemas import Contract


class Intent(str, Enum):
    INVENTORY = 'INVENTORY'
    DEMAND = 'DEMAND'
    PRICING = 'PRICING'
    ORDER = 'ORDER'
    SUPPLY_CHAIN = 'SUPPLY_CHAIN'
    CUSTOMER_SUPPORT = 'CUSTOMER_SUPPORT'
    RETURNS = 'RETURNS'
    ANALYTICS = 'ANALYTICS'
    MULTI_AGENT = 'MULTI_AGENT'
    UNKNOWN = 'UNKNOWN'


class RouteSettings(Contract):
    confidence_threshold: float = Field(default=0.65, gt=0, le=1)
    max_agents: int = Field(default=8, ge=1, le=8)


class Task(Contract):
    step_id: str
    intent: Intent
    agent: str
    depends_on: list[str] = Field(default_factory=list)
    subqueries: list[str]
    reason_codes: list[str]


class RoutingPlan(Contract):
    intent: Intent
    candidates: list[Intent]
    confidence: float = Field(ge=0, le=1)
    requires_human: bool
    reason: str
    tasks: list[Task] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    classifier_version: str = 'retail-rules-v1'
    confidence_kind: str = 'heuristic_not_calibrated_probability'
