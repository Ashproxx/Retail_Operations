"""Structured branch-local adapter; natural-language integration is deferred."""
from time import perf_counter
from app.agents.base_agent import BaseAgent
from app.api.schemas import AgentResult, Evidence, AuditEvent, QueryRequest, RequestContext, Role
from app.core.exceptions import DataValidationError
from app.agents.support.domain import Policy, Query, evaluate

class Agent(BaseAgent):
    def __init__(self, records=None):
        self.records=[Policy.model_validate(r).model_copy(deep=True) for r in (records or [])]

    async def run(self, query: QueryRequest, context: RequestContext) -> AgentResult:
        if query.session_id!=context.session_id:raise DataValidationError('Session mismatch')
        started=perf_counter()
        request=Query.model_validate_json(query.message)
        requested=getattr(request,'store_id',None)
        if context.role!=Role.ADMIN and requested is not None and requested not in context.store_ids:
            return AgentResult(agent='support',request_id=context.request_id,status='escalated',
                               summary='Requested store is outside the trusted scope.',confidence=0)
        records=[r for r in self.records if context.role==Role.ADMIN or r.store_id in context.store_ids]
        data=evaluate(records,request)
        status=data.pop('status','success')
        elapsed=(perf_counter()-started)*1000
        fixture=any(getattr(r,'fixture',False) for r in records)
        audit=AuditEvent(request_id=context.request_id,session_id=context.session_id,user_role=context.role,
            agents_called=['support'],tools_called=['support.evaluate'],confidence=0,latency_ms=elapsed,final_status=status)
        data['audit']=audit.model_dump(mode='json')
        data['fixture']=fixture
        return AgentResult(agent='support',request_id=context.request_id,status=status,
            summary='Structured support analysis.' if status=='success' else 'Insufficient or missing domain data.',
            data=data,requires_other_agents=data.get('handoffs',[]),recommended_actions=['Human support review required.'] if data.get('requires_human') else [],evidence=[Evidence(document_id=s['document_id'],source=s['source'],content_hash=s['content_hash']) for s in data.get('sources',[])],confidence=0,latency_ms=elapsed,tool_calls=['support.evaluate'],
            warnings=(['Synthetic fixtures; not production data.'] if fixture else [])+
                     ['No calibrated prediction confidence; inspect assumptions and source metadata.'])
