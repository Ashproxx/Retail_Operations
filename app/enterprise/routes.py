"""Separate authenticated data APIs and public, data-free workspace shells."""
from pathlib import Path
from fastapi import APIRouter,Request,HTTPException,Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.integration.routes import context,audit_operation
from app.enterprise.contracts import WorkspaceTurn
from app.employees.security import audit
from typing import Literal
from collections import Counter
from sqlalchemy import select
from app.api.schemas import Role
from app.enterprise.data import Product, Sale
from app.enterprise.retail import filters

router=APIRouter(prefix='/api')
ASSETS=Path(__file__).parent/'static'


def page():
    return FileResponse(ASSETS/'index.html',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"})


def mount(api):
    api.include_router(router)
    api.mount('/workspace-assets',StaticFiles(directory=ASSETS),name='workspace-assets')
    for path in ['/models','/retail','/employees','/employee-work','/management','/datasets']:
        api.add_api_route(path,page,methods=['GET'],include_in_schema=False)


@router.get('/datasets/{kind}')
def dataset(request:Request,kind:Literal['products','employees'],offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100)):
    ctx=context(request,'dataset-browser');runtime=request.app.state.runtime
    subjects=[];fields=[];status='denied'
    try:
        if kind=='products':
            clauses=filters(ctx,{})
            with request.app.state.database.session() as s:
                records=list(s.scalars(select(Product).where(Product.sku_id.in_(select(Sale.sku_id).where(*clauses))).order_by(Product.sku_id)))
            counts=dict(Counter(r.payload.get('normalized_category') or r.payload.get('category') or 'Not recorded' for r in records))
            fields=['category','style_name','gender','color','size']
            rows=[{'sku_id':r.sku_id,**{k:r.payload.get(k) for k in fields}} for r in records[offset:offset+limit]]
            result={'total':len(records),'metrics':{'Catalog products':len(records)},'groups':counts,'rows':rows,
                    'note':'Products recorded in authorized sales history. On-hand inventory was not supplied; these counts are distinct SKUs, not stock units.',
                    'chart_title':'Product catalog by category','source':'POC Navi Mumbai Sales Dataset'}
        else:
            service=request.app.state.employees
            overview=service.overview(ctx)
            records=service.rows(ctx,detail=True) if ctx.role!=Role.ANALYST else []
            page=records[offset:offset+limit]
            fields=['full_name','store_location','city','department','designation','shift','employment_status']
            subjects=[r['employee_id'] for r in page]
            result={'total':len(records) if ctx.role!=Role.ANALYST else None,
                    'metrics':{k:v for k,v in overview['metrics'].items() if k in ['Employees','Active employees','Privacy']},
                    'groups':overview['groups'].get('employment_status',{}),
                    'rows':[{k:r.get(k) for k in fields} for r in page],
                    'note':'Recorded employment status from the supplied HR snapshot, not live attendance or who is on duty.' + (' Your role allows aggregates only.' if ctx.role==Role.ANALYST else ''),
                    'chart_title':'Staff by recorded employment status','source':'POC Navi Mumbai Employee Dataset'}
        status='success'
        return {**result,'offset':offset,'limit':limit,'synthetic':True}
    finally:
        audit(runtime,ctx,'dataset.'+kind,status,subjects,fields if status=='success' else [])


@router.get('/retail/options')
def retail_options(request:Request):
    ctx=context(request,'retail-discovery');status='denied'
    try:
        result=request.app.state.retail.options(ctx);status='success';return result
    finally:audit_operation(request.app.state.runtime,ctx,'retail.discover',status)


@router.post('/retail/chat')
def retail_chat(body:WorkspaceTurn,request:Request):
    ctx=context(request,body.session_id)
    try:
        with request.app.state.workspace_lock:return request.app.state.retail.run(body,ctx)
    except ValueError:raise HTTPException(422,'Choose a valid option, date or bounded forecast horizon.') from None


@router.get('/employees/options')
def employee_options(request:Request):
    ctx=context(request,'employee-discovery');status='denied'
    try:
        result=request.app.state.employees.options(ctx);status='success';return result
    finally:audit(request.app.state.runtime,ctx,'employee.discover',status,fields=['aggregate_dimensions'] if status=='success' else [])


@router.get('/employees/search')
def employee_search(request:Request,q:str=Query(min_length=1,max_length=200)):
    return request.app.state.employees.search(q,context(request,'employee-search'))


@router.get('/employees/overview')
def employee_overview(request:Request):
    ctx=context(request,'employee-overview');result=None
    try:
        result=request.app.state.employees.overview(ctx);return result
    finally:audit(request.app.state.runtime,ctx,'employee.overview','success' if result else 'denied',fields=list((result or {}).get('metrics',{})))


@router.post('/employees/chat')
def employee_chat(body:WorkspaceTurn,request:Request):
    ctx=context(request,body.session_id)
    try:
        with request.app.state.workspace_lock:return request.app.state.employees.run(body,ctx)
    except ValueError:raise HTTPException(422,'Choose a valid employee option.') from None
