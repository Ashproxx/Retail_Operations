"""Separate authenticated data APIs and public, data-free workspace shells."""
from pathlib import Path
from fastapi import APIRouter,Request,HTTPException,Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.integration.routes import context,audit_operation
from app.enterprise.contracts import WorkspaceTurn
from app.employees.security import audit

router=APIRouter(prefix='/api')
ASSETS=Path(__file__).parent/'static'


def page():
    return FileResponse(ASSETS/'index.html',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"})


def mount(api):
    api.include_router(router)
    api.mount('/workspace-assets',StaticFiles(directory=ASSETS),name='workspace-assets')
    for path in ['/models','/retail','/employees','/employee-work','/management']:
        api.add_api_route(path,page,methods=['GET'],include_in_schema=False)


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
