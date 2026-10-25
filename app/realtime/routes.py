import asyncio
from datetime import datetime,timezone
import hashlib,hmac,json
from fastapi import APIRouter,Request,HTTPException,Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import ValidationError
from app.integration.routes import context,audit_operation
from app.realtime.stream.ingest import Event

router=APIRouter(prefix='/api')


@router.get('/realtime/status')
def status(request:Request):
    ctx=context(request,'realtime-status')
    result=request.app.state.realtime.status(ctx)
    audit_operation(request.app.state.runtime,ctx,'realtime.status')
    return JSONResponse(result,headers={'Cache-Control':'no-store'})


@router.post('/stream/ingest')
async def ingest(request:Request):
    ctx=context(request,'stream-ingest');service=request.app.state.realtime;settings=service.settings
    if settings.stream_mode!='webhook':raise HTTPException(403,'Webhook mode is disabled')
    key=settings.stream_hmac_key
    if not key or len(key.get_secret_value())<32:raise HTTPException(503,'Configure an HMAC key of at least 32 characters')
    body=b''
    async for chunk in request.stream():
        body+=chunk
        if len(body)>65536:raise HTTPException(413,'Event too large')
    stamp=request.headers.get('X-Event-Timestamp','');signature=request.headers.get('X-Event-Signature','')
    try:age=abs(datetime.now(timezone.utc).timestamp()-int(stamp))
    except ValueError:raise HTTPException(401,'Invalid event signature') from None
    expected=hmac.new(key.get_secret_value().encode(),stamp.encode()+b'.'+body,hashlib.sha256).hexdigest()
    if age>300 or not hmac.compare_digest(expected,signature):
        audit_operation(request.app.state.runtime,ctx,'stream.ingest','denied')
        raise HTTPException(401,'Invalid event signature')
    try:
        event=Event.model_validate_json(body)
        if event.synthetic:raise ValueError('Webhook cannot claim simulator provenance')
        result=service.ingestor.ingest(event,ctx)
    except (ValueError,ValidationError):raise HTTPException(422,'Invalid or conflicting event') from None
    audit_operation(request.app.state.runtime,ctx,'stream.ingest')
    return result


@router.get('/stream/sales')
async def sales(request:Request,after:int=Query(0,ge=0),once:bool=False):
    service=request.app.state.realtime
    ctx=context(request,'stream-sales');service.rows(ctx,after)
    async def generate():
        cursor=after
        while not await request.is_disconnected():
            # Recheck expiry and scope on each poll, not only when the stream opens.
            try:ctx=context(request,'stream-sales');rows=service.rows(ctx,cursor)
            except Exception:
                yield 'event: authentication-required\ndata: {}\n\n';return
            for row in rows:
                cursor=row.id
                data={'id':row.id,'store_id':row.store_id,'quantity':row.quantity,'occurred_at':row.occurred_at,'received_at':row.received_at,'synthetic':row.synthetic,'source':row.source}
                yield f'id: {cursor}\ndata: {json.dumps(data)}\n\n'
            if once:return
            yield ': heartbeat\n\n'
            await asyncio.sleep(2)
    return StreamingResponse(generate(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
