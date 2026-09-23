from abc import ABC, abstractmethod
from app.api.schemas import AgentResult, QueryRequest, RequestContext


class BaseAgent(ABC):
    """All domain branches implement this asynchronous, structured contract."""
    @abstractmethod
    async def run(self, query: QueryRequest, context: RequestContext) -> AgentResult:
        """Use trusted context for authorization; never fabricate missing data."""
        raise NotImplementedError
