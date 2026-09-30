"""Authenticated conversational API; all identity and scope come from server grants."""
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.integration.routes import context, audit_operation
from app.conversation.contracts import Turn
from app.conversation.service import ConversationService
from app.conversation.catalog import Catalog
from app.security.policy import PERMISSIONS

router = APIRouter(prefix='/api/conversation')

@router.post('')
async def conversation(body: Turn, request: Request):
    principal = context(request, body.session_id)
    if not hasattr(request.app.state, 'conversation'):
        request.app.state.conversation = ConversationService(request.app.state.runtime)
    try:
        return await request.app.state.conversation.run(body, principal)
    except ValueError:
        raise HTTPException(status_code=422, detail='This selection cannot be analysed. Choose a listed option, a narrower period, or valid ISO dates.') from None

@router.get('/options')
def discover(request: Request, session_id: str = 'discovery'):
    principal = context(request, session_id)
    catalog = Catalog(request.app.state.runtime, principal)
    allowed=PERMISSIONS[principal.role]
    action=next((a for a in ['analytics.read','inventory.read','forecast.read'] if a in allowed),None)
    if action:
        rows=catalog.observations(action=action)
    else:
        agent='customer-service' if 'support.read' in allowed else 'order-fulfillment'
        records=request.app.state.runtime.repository.records(agent,principal)
        stores=request.app.state.runtime.repository.stores(principal)
        audit_operation(request.app.state.runtime, principal, 'conversation.discover')
        return {'locations':sorted({stores.get(r['store_id'],'Authorized location') for r in records}), 'categories':[], 'date_range':None,'fixture':any(r.get('fixture') for r in records)}
    audit_operation(request.app.state.runtime, principal, 'conversation.discover')
    return {'locations': catalog.discover('store_location', rows),
            'categories': catalog.discover('normalized_category', rows),
            'date_range': [min(r['date'] for r in rows), max(r['date'] for r in rows)] if rows else None,
            'fixture': any(r.get('fixture') for r in rows)}

def mount_assistant(api):
    assets = Path(__file__).parent / 'static'
    if not assets.exists(): return
    api.mount('/assistant-assets', StaticFiles(directory=assets), name='assistant-assets')
    @api.get('/assistant', include_in_schema=False)
    def assistant():
        return FileResponse(assets / 'index.html', headers={'Cache-Control':'no-store',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
            'X-Content-Type-Options':'nosniff'})
