from datetime import date
from uuid import UUID
from fastapi import APIRouter, Request
from app.api.schemas import AuditEvent, ChatResponse
from app.security.policy import AuthenticationFailed, authorize
from app.security.audit import verify_chain
from app.integration.contracts import ChatQuery, DirectQuery, IngestRequest, RagQuery, Feedback

router=APIRouter(prefix='/api')

def context(request,session_id):
    authorization=request.headers.get('Authorization','')
    scheme,_,token=authorization.partition(' ')
    if scheme.lower()!='bearer' or not token:raise AuthenticationFailed('Authentication required')
    ctx=request.app.state.runtime.auth.authenticate(token,session_id)
    ctx.request_id=UUID(request.state.request_id)
    return ctx

def audit_operation(runtime,ctx,tool,status='success',documents=None,iterations=0):
    runtime.audit.append(AuditEvent(request_id=ctx.request_id,session_id=ctx.session_id,user_role=ctx.role,
        tools_called=[tool],documents_retrieved=documents or [],rag_iterations=iterations,
        confidence=0,latency_ms=0,final_status=status))

@router.post('/chat',response_model=ChatResponse)
async def chat(body:ChatQuery,request:Request):
    ctx=context(request,body.session_id)
    return await request.app.state.runtime.orchestrator.run(body,ctx)

@router.post('/query',response_model=ChatResponse)
async def query(body:DirectQuery,request:Request):
    ctx=context(request,body.session_id)
    return await request.app.state.runtime.orchestrator.run(body,ctx)

@router.post('/forecast',response_model=ChatResponse)
async def forecast(body:ChatQuery,request:Request):
    ctx=context(request,body.session_id)
    return await request.app.state.runtime.orchestrator.run(DirectQuery(session_id=body.session_id,
        agent='demand-forecasting',parameters=body.parameters),ctx)

@router.get('/inventory/low-stock',response_model=ChatResponse)
async def low_stock(request:Request,session_id:str='inventory',store_id:str|None=None,as_of:date|None=None):
    ctx=context(request,session_id)
    params={'action':'low_stock'}
    if store_id is not None:params['store_id']=store_id
    if as_of is not None:params['as_of']=as_of.isoformat()
    return await request.app.state.runtime.orchestrator.run(DirectQuery(session_id=session_id,agent='inventory',parameters=params),ctx)

@router.get('/inventory/{store_id}',response_model=ChatResponse)
async def inventory(store_id:str,request:Request,session_id:str='inventory',as_of:date|None=None):
    ctx=context(request,session_id)
    params={'store_id':store_id}
    if as_of is not None:params['as_of']=as_of.isoformat()
    return await request.app.state.runtime.orchestrator.run(DirectQuery(session_id=session_id,agent='inventory',parameters=params),ctx)

@router.get('/analytics/summary',response_model=ChatResponse)
async def analytics(request:Request,session_id:str='analytics',store_id:str|None=None,start:date|None=None,end:date|None=None):
    ctx=context(request,session_id)
    params={k:v.isoformat() if isinstance(v,date) else v for k,v in {'store_id':store_id,'start':start,'end':end}.items() if v is not None}
    return await request.app.state.runtime.orchestrator.run(DirectQuery(session_id=session_id,agent='analytics-reporting',parameters=params),ctx)

@router.post('/rag/ingest')
async def rag_ingest(body:IngestRequest,request:Request):
    ctx=context(request,body.session_id);runtime=request.app.state.runtime
    try:
        count=runtime.rag.ingest(body.document,ctx)
        audit_operation(runtime,ctx,'rag.ingest',documents=[body.document.document_id])
        return {'chunks_loaded':count,'fixture':body.document.fixture}
    except Exception:
        audit_operation(runtime,ctx,'rag.ingest','error')
        raise

@router.post('/rag/query')
async def rag_query(body:RagQuery,request:Request):
    ctx=context(request,body.session_id);runtime=request.app.state.runtime
    try:
        result=runtime.rag.query(body.question,ctx,body.store_id,body.domain)
        audit_operation(runtime,ctx,'rag.retrieve_verified',result.status,[h.chunk.document_id for h in result.sources],result.iterations)
        return result
    except Exception:
        audit_operation(runtime,ctx,'rag.retrieve_verified','error')
        raise

@router.get('/audit')
async def audit(request:Request,session_id:str='audit',limit:int=100):
    ctx=context(request,session_id);runtime=request.app.state.runtime
    authorize(ctx,'audit.read')
    rows=runtime.audit.read()
    return {'events':rows[-max(1,min(limit,1000)):],'anchor':verify_chain(rows),
            'limitation':'Retain the anchor outside this server to detect rollback across restarts.'}

@router.post('/feedback')
async def feedback(body:Feedback,request:Request):
    ctx=context(request,body.session_id);runtime=request.app.state.runtime
    runtime.repository.feedback(ctx,body)
    audit_operation(runtime,ctx,'feedback.record')
    return {'recorded':True}
