"""Structured branch-local adapter; natural-language integration is deferred."""
from time import perf_counter
from app.agents.base_agent import BaseAgent
from app.api.schemas import AgentResult, AuditEvent, QueryRequest, RequestContext, Role
from app.core.exceptions import DataValidationError
from app.agents.supply.domain import Vendor, Query, evaluate

class Agent(BaseAgent):
    def __init__(self, records=None):
        self.records=[Vendor.model_validate(r).model_copy(deep=True) for r in (records or [])]

    async def run(self, query: QueryRequest, context: RequestContext) -> AgentResult:
        if query.session_id!=context.session_id:raise DataValidationError('Session mismatch')
        started=perf_counter()
        request=Query.model_validate_json(query.message)
        requested=getattr(request,'store_id',None)
        if context.role!=Role.ADMIN and requested is not None and requested not in context.store_ids:
            return AgentResult(agent='supply',request_id=context.request_id,status='escalated',
                               summary='Requested store is outside the trusted scope.',confidence=0)
        records=[r for r in self.records if context.role==Role.ADMIN or r.store_id in context.store_ids]
        data=evaluate(records,request)
        status=data.pop('status','success')
        elapsed=(perf_counter()-started)*1000
        fixture=any(getattr(r,'fixture',False) for r in records)
        audit=AuditEvent(request_id=context.request_id,session_id=context.session_id,user_role=context.role,
            agents_called=['supply'],tools_called=['supply.evaluate'],confidence=0,latency_ms=elapsed,final_status=status)
        data['audit']=audit.model_dump(mode='json')
        data['fixture']=fixture
        return AgentResult(agent='supply',request_id=context.request_id,status=status,
            summary='Structured supply analysis.' if status=='success' else 'Insufficient or missing domain data.',
            data=data,confidence=0,latency_ms=elapsed,tool_calls=['supply.evaluate'],
            warnings=(['Synthetic fixtures; not production data.'] if fixture else [])+
                     ['No calibrated prediction confidence; inspect assumptions and source metadata.'])
