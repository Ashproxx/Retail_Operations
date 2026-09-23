"""LangGraph composition with bounded dispatch and conservative aggregation."""
import asyncio
import hashlib
import json
import re
from time import perf_counter
from typing import TypedDict
from pydantic import ValidationError
from langgraph.graph import StateGraph, START, END
from langsmith import tracing_context
from app.api.schemas import AgentResult, AuditEvent, ChatResponse, Evidence, QueryRequest
from app.orchestration.router.agent import RouterAgent
from app.orchestration.router.contracts import RoutingPlan
from app.integration.registry import REGISTRY, contracts
from app.integration.parameters import extract, prepare, Clarification, routing_text
from app.core.exceptions import ComponentUnavailableError
from app.security.policy import AccessDenied

class WorkflowState(TypedDict, total=False):
    query: object
    context: object
    message: str
    parameters: dict
    targets: list[str]
    plan: dict
    results: list
    clarification: str
    response: object
    started: float


def aggregate(results):
    conflicts=[]
    by_id={r['target']:r for r in results}
    inventory=by_id.get('inventory',{}).get('result')
    pricing=by_id.get('pricing-promotions',{}).get('result')
    if inventory and pricing:
        risky=any(i.get('stockout_risk') or i.get('stockout') for i in inventory.data.get('items',[]))
        recommendation=pricing.data.get('recommendation') or {}
        if risky and float(recommendation.get('applied_discount_pct','0'))>0:
            conflicts.append('A discount recommendation conflicts with observed stock risk; human review is required before applying either recommendation.')
    if any(r['result'].data.get('reason')=='conflicting_evidence' for r in results):
        conflicts.append('Conflicting policy evidence requires human review.')
    return conflicts

def cross_agent_actions(results):
    by_id={r['target']:r['result'] for r in results}
    inventory=by_id.get('inventory');forecast=by_id.get('demand-forecasting')
    if not inventory or not forecast or inventory.status!='success' or forecast.status!='success':return []
    if any(i.get('below_reorder_point') for i in inventory.data.get('items',[])) and forecast.data.get('mean_trend_change',0)>0:
        return [{'action':'Review replenishment quantities and supplier capacity before running promotions.',
                 'based_on':['inventory','demand-forecasting'], 'advisory_only':True,
                 'limitation':'Forecast uncertainty is uncalibrated; no purchase or price change was executed.'}]
    return []

class Orchestrator:
    def __init__(self, repository, audit, rag=None, provider=None):
        self.repository,self.audit,self.rag,self.provider=repository,audit,rag,provider
        self.router=RouterAgent()
        graph=StateGraph(WorkflowState)
        graph.add_node('route',self.route)
        graph.add_node('execute',self.execute)
        graph.add_node('aggregate',self.finish)
        graph.add_edge(START,'route')
        graph.add_conditional_edges('route',lambda s:'aggregate' if s.get('clarification') else 'execute')
        graph.add_edge('execute','aggregate');graph.add_edge('aggregate',END)
        self.graph=graph.compile()
        self.lock=asyncio.Lock()

    async def route(self,state):
        query,context=state['query'],state['context']
        message=getattr(query,'message','')
        supplied=query.parameters.copy()
        previous=self.repository.memory(context)
        try:
            params=extract(message,supplied,self.repository.stores(context))
            if hasattr(query,'agent'):
                if query.agent not in REGISTRY:raise Clarification('Unknown agent; select a registered agent ID.')
                _,schema,_=contracts(query.agent)
                if not set(supplied)<=set(schema.model_fields):raise Clarification('Parameters do not match the selected agent schema.')
                targets=[query.agent];plan={'source':'explicit_structured_request','tasks':targets}
            elif re.fullmatch(r'\s*what about .+?\s*[?]?\s*',message,re.I):
                if not previous:raise Clarification('No prior intent in this authenticated session; state the requested operation.')
                if 'store_id' not in params:raise Clarification('Provide the store_id for this follow-up.')
                params={**previous['parameters'],**params}
                message=previous['intent_message']
                targets=previous['targets'];plan={'source':'scoped_session_followup','tasks':targets}
            else:
                routed=await self.router.run(QueryRequest(message=routing_text(message),session_id=context.session_id),context)
                routing=RoutingPlan.model_validate(routed.data['plan'])
                plan=routing.model_dump(mode='json')
                if routing.requires_human:raise Clarification('Please clarify the retail operation: '+routing.reason)
                targets=[task.agent for task in routing.tasks]
            return {'message':message,'parameters':params,'targets':targets,'plan':plan,'results':[]}
        except Clarification as exc:
            return {'clarification':str(exc),'targets':[],'plan':{'source':'clarification'},'results':[]}

    async def execute(self,state):
        context=state['context'];results=[]
        for target in state['targets'][:8]:
            entry=REGISTRY[target]
            try:
                rows=self.repository.records(target,context,state['parameters'].get('store_id'))
                request,notes=prepare(target,state['message'],state['parameters'],rows)
                _,_,adapter=contracts(target)
                result=await adapter(rows).run(QueryRequest(message=request.model_dump_json(),session_id=context.session_id),context)
                result.warnings.extend(notes)
                # Preserve observed provenance; do not relabel model output as database evidence.
                result.data['parameters_used']=request.model_dump(mode='json')
                result.data['depends_on_results']=[r['target'] for r in results]
                result.data['registry_id']=target
                if target=='customer-service' and self.rag is not None:
                    try:
                        rag=self.rag.query(request.question,context,request.store_id,'support')
                        result.data['rag']=rag.model_dump(mode='json')
                        result.evidence.extend(Evidence(document_id=h.chunk.document_id,source=h.chunk.source,
                            chunk_id=h.chunk.chunk_id,content_hash=h.chunk.content_hash) for h in rag.sources)
                        result.tool_calls.append('rag.retrieve_verified')
                        rag_conflict=len({h.chunk.document_id for h in rag.sources})>1
                        if rag_conflict:
                            result.status='escalated'
                            result.data['reason']='conflicting_evidence'
                            result.data['requires_human']=True
                            result.data['answer']='Multiple relevant documents require human review; no policy was selected.'
                        if not rag_conflict and result.data.get('reason')!='conflicting_evidence' and rag.status=='evidence_found':
                            # RAG excerpts are evidence; they do not assert approved policy validity.
                            result.data['answer']=rag.answer
                            result.status='escalated' if result.data['triage']['priority']=='human_review' else 'success'
                            result.data['requires_human']=result.status!='success'
                            if result.status=='success':result.recommended_actions=[]
                    except ComponentUnavailableError:
                        result.warnings.append('Local RAG model/key is not configured; no external fallback.')
                results.append({'target':target,'result':result})
            except AccessDenied:
                result=AgentResult(agent=entry.module,request_id=context.request_id,status='escalated',
                    summary='This operation is outside your authorized role or store scope.',confidence=0,
                    data={'reason':'access_denied','registry_id':target})
                results.append({'target':target,'result':result})
            except (Clarification,ValidationError) as exc:
                message=str(exc) if isinstance(exc,Clarification) else 'Invalid parameters; check the documented domain schema.'
                results.append({'target':target,'result':AgentResult(agent=entry.module,request_id=context.request_id,
                    status='escalated',summary=message,confidence=0,data={'reason':'clarification_required','registry_id':target})})
            except Exception:
                results.append({'target':target,'result':AgentResult(agent=entry.module,request_id=context.request_id,
                    status='error',summary='Agent execution failed; no result was inferred.',confidence=0,
                    data={'reason':'component_error','registry_id':target})})
        return {'results':results}

    async def finish(self,state):
        context=state['context'];results=state.get('results',[])
        conflicts=aggregate(results)
        failed=any(r['result'].status!='success' for r in results)
        requires_human=bool(state.get('clarification') or conflicts or failed)
        status='escalated' if requires_human else 'success'
        if any(r['result'].status=='error' for r in results):status='error'
        summaries=[]
        for row in results:
            result=row['result'];data=result.data
            detail=data.get('answer',result.summary)
            if row['target']=='inventory' and result.status=='success':
                detail=f"{len(data['items'])} matching inventory items across {len(data['store_available_totals'])} stores."
            elif row['target']=='analytics-reporting' and result.status=='success':
                detail=f"Units sold: {data['summary']['units_sold']}; observed sales INR {data['summary']['sales_inr']}."
            elif row['target']=='demand-forecasting' and result.status=='success':
                detail=f"{len(data['forecast'])}-day baseline forecast; uncertainty is uncalibrated."
            summaries.append(row['target']+': '+detail)
        answer=state.get('clarification') or '\n'.join(summaries)
        if conflicts:answer+='\n'+'\n'.join(conflicts)
        sources=[e for row in results for e in row['result'].evidence]
        fixture=any(row['result'].data.get('fixture') or any(h.get('chunk',{}).get('fixture') for h in row['result'].data.get('rag',{}).get('sources',[])) for row in results)
        if fixture:answer='SYNTHETIC FIXTURE RESULTS — not production data.\n'+answer
        data={'request_id':str(context.request_id),'status':status,'requires_human':requires_human,
              'plan':state.get('plan',{}),'results':{r['target']:r['result'].model_dump(mode='json') for r in results},
              'conflicts':conflicts,'fixture':fixture,'operational_write_performed':False,
              'confidence_kind':'uncalibrated; zero does not negate deterministic calculations',
              'recommended_actions':cross_agent_actions(results)}
        if getattr(state['query'],'draft_with_llm',False) and not requires_human:
            try:
                if self.provider is None:raise ComponentUnavailableError('Provider not configured')
                # A separate unverified draft cannot overwrite facts, control tools, or clear escalation.
                data['unverified_llm_draft']=await self.provider.draft(answer)
            except ComponentUnavailableError:data['llm_warning']='Local model unavailable; deterministic results are retained.'
        event=AuditEvent(request_id=context.request_id,session_id=context.session_id,user_role=context.role,
            router_decision=state.get('targets',[]),agents_called=['router']+[r['target'] for r in results if 'parameters_used' in r['result'].data],
            tools_called=[t for r in results for t in r['result'].tool_calls],documents_retrieved=[e.document_id for e in sources],
            rag_iterations=sum(r['result'].data.get('rag',{}).get('iterations',0) for r in results),
            confidence=0,latency_ms=(perf_counter()-state['started'])*1000,final_status=status)
        self.audit.append(event)
        self.repository.receipt(context)
        if not requires_human:
            self.repository.remember(context,{'targets':state['targets'],'parameters':{**state['parameters'],**({'action':next(r['result'].data['parameters_used']['action'] for r in results if r['target']=='inventory')} if any(r['target']=='inventory' for r in results) else {})},
                # Retain minimal deterministic intent labels, never raw user chat/documents.
                'intent_message':' '.join(state['targets'])+' '+state['parameters'].get('action',
                    next((r['result'].data.get('parameters_used',{}).get('action','') for r in results if r['target']=='inventory'),''))})
        return {'response':ChatResponse(session_id=context.session_id,agents_used=event.agents_called,answer=answer,
                                      data=data,sources=sources,confidence=0)}

    async def run(self,query,context):
        async with self.lock:
            with tracing_context(enabled=False):
                try:
                    state=await self.graph.ainvoke({'query':query,'context':context,'started':perf_counter()},config={'callbacks':[]})
                except Exception:
                    self.audit.append(AuditEvent(request_id=context.request_id,session_id=context.session_id,
                        user_role=context.role,confidence=0,latency_ms=0,final_status='error'))
                    raise
            return state['response']
