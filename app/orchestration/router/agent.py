from collections.abc import Callable
from time import perf_counter
from langsmith import tracing_context
from app.agents.base_agent import BaseAgent
from app.api.schemas import AgentResult, AuditEvent, QueryRequest, RequestContext
from app.core.config import Settings
from app.core.exceptions import DataValidationError
from app.core.logging import configure_logging
from app.orchestration.router.contracts import RouteSettings
from app.orchestration.router.graph import build_graph


class RouterAgent(BaseAgent):
    def __init__(self, settings: RouteSettings | None = None, audit_sink: Callable[[AuditEvent],None] | None = None):
        self.settings = settings or RouteSettings(confidence_threshold=Settings().routing_confidence_threshold)
        self.graph = build_graph(self.settings)
        self.audit_sink = audit_sink
        self.logger = configure_logging('INFO')

    async def run(self, query: QueryRequest, context: RequestContext) -> AgentResult:
        if query.session_id != context.session_id:
            raise DataValidationError('Session context mismatch')
        started = perf_counter()
        # No checkpointer or callbacks configured; raw query state is transient.
        with tracing_context(enabled=False):
            state = await self.graph.ainvoke({'message':query.message}, config={'callbacks': []})
        plan = state['plan']
        elapsed = (perf_counter()-started)*1000
        status = 'escalated' if plan.requires_human else 'success'
        event = AuditEvent(request_id=context.request_id,session_id=context.session_id,user_role=context.role,
                          router_decision=[i.value for i in plan.candidates],agents_called=['router'],
                          confidence=plan.confidence,latency_ms=elapsed,final_status=status)
        warnings = ['Routing confidence is heuristic, not a calibrated probability.',
                    'Plan only: downstream agents were not executed.']
        if self.audit_sink:
            # Fail visibly if a configured audit sink fails; do not silently lose audit events.
            self.audit_sink(event)
        else:
            warnings.append('No durable audit sink configured; audit metadata returned to caller.')
        self.logger.info('routing',extra={'event':'routing_'+plan.reason,'request_id':str(context.request_id)})
        return AgentResult(agent='router',request_id=context.request_id,status=status,
            summary='Human clarification required.' if plan.requires_human else 'Proposed agent execution plan ready.',
            confidence=plan.confidence,latency_ms=elapsed,warnings=warnings,
            data={'plan':plan.model_dump(mode='json'),'audit':event.model_dump(mode='json')},
            requires_other_agents=[t.agent for t in plan.tasks])
