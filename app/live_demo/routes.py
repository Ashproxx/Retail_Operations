from datetime import date, datetime, timedelta
import json
from typing import Literal
from fastapi import HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.api.schemas import Role
from app.enterprise.retail import permits
from app.integration.routes import context, audit_operation
from app.security.policy import AccessDenied
from app.live_demo.config import Config, TZ, instant, factors
from app.live_demo.store import connect, state, now_utc
from app.live_demo.worker import correct


class Correction(BaseModel):
    event_id: str=Field(min_length=1,max_length=64)
    reason: str=Field(min_length=1,max_length=300)
    replacement_units: int|None=Field(None,ge=1,le=100)


def clauses(ctx,store='',category='',source='all',alias='e'):
    permits(ctx);parts=['1=1'];args=[]
    if ctx.role!=Role.ADMIN:
        parts.append(alias+'.store_id IN ('+','.join('?' for _ in ctx.store_ids)+')');args.extend(ctx.store_ids)
    if store:
        if ctx.role!=Role.ADMIN and store not in ctx.store_ids: raise AccessDenied('Outside store scope')
        parts.append(alias+'.store_id=?');args.append(store)
    if category:
        parts.append(alias+".sku_id IN (SELECT sku_id FROM retail_products WHERE COALESCE(json_extract(payload,'$.normalized_category'),json_extract(payload,'$.category'),'Unknown')=?)")
        args.append(category)
    if source=='generated': parts.append(alias+'.synthetic=1')
    if source=='imported': parts.append(alias+".source='copied-unverified'")
    return ' AND '.join(parts),args


def totals(db,where,args,start,end,as_known):
    row=dict(db.execute("SELECT COUNT(*) records,SUM(quantity) units,SUM(net_paise) net_paise,COUNT(DISTINCT CASE WHEN kind IN('sale','imported') THEN order_id END) orders,SUM(CASE WHEN kind IN('return','damaged_return') THEN -quantity ELSE 0 END) returned_units FROM demo_events e WHERE "+where+
        " AND e.kind IN('sale','imported','return','damaged_return','reversal') AND occurred_at>=? AND occurred_at<=? AND received_at<=?",
        [*args,start.isoformat(),end.isoformat(),as_known.isoformat()]).fetchone())
    if row['records']==0:
        row.update(units=None,net_paise=None,orders=None,returned_units=None)
    return row


def install(api,path):
    from contextlib import asynccontextmanager
    original=api.router.lifespan_context
    @asynccontextmanager
    async def lifespan(app):
        async with original(app):
            app.state.retail.live_demo_path=path
            yield
    api.router.lifespan_context=lifespan
    @api.get('/api/demo/enabled')
    def enabled(): return {'enabled':True,'banner':'SIMULATED DEMO DATA'}

    @api.get('/api/demo/summary')
    def summary(request:Request,start:date|None=None,end:date|None=None,store:str='',category:str='',sku:str='',
                source:Literal['all','generated','imported']='all'):
        ctx=context(request,'live-demo');now=now_utc();today=now.astimezone(TZ).date()
        start=start or today;end=end or today
        if end<start or (end-start).days>800 or end>today: raise HTTPException(422,'Use a historical range of at most 800 days')
        where,args=clauses(ctx,store,category,source)
        if sku: where+=' AND e.sku_id=?';args.append(sku)
        low=instant(start,0);high=min(now,instant(end+timedelta(days=1),0)-timedelta(microseconds=1))
        with connect(path) as db:
            cfg=Config.model_validate(state(db,'config'))
            result=totals(db,where,args,low,high,now)
            current=totals(db,where,args,instant(today,0),now,now)
            yesterday=totals(db,where,args,instant(today-timedelta(days=1),0),now-timedelta(days=1),now)
            trends=[dict(r) for r in db.execute("SELECT business_date day,SUM(quantity) units,SUM(net_paise) net_paise FROM demo_events e WHERE "+where+
                " AND kind IN('sale','imported','return','damaged_return','reversal') AND occurred_at BETWEEN ? AND ? GROUP BY business_date ORDER BY business_date",[*args,low.isoformat(),high.isoformat()])]
            monthly=[dict(r) for r in db.execute("SELECT substr(business_date,1,7) month,SUM(quantity) units,SUM(net_paise) net_paise FROM demo_events e WHERE "+where+
                " AND kind IN('sale','imported','return','damaged_return','reversal') AND occurred_at BETWEEN ? AND ? GROUP BY month ORDER BY month",[*args,low.isoformat(),high.isoformat()])]
            stock_where,stock_args=clauses(ctx,store,category,'all')
            if sku: stock_where+=' AND e.sku_id=?';stock_args.append(sku)
            stock_query="SELECT store_id,sku_id,CASE WHEN SUM(CASE WHEN kind='opening' THEN 1 ELSE 0 END)>0 THEN SUM(stock_delta) ELSE NULL END available FROM demo_events e WHERE "+stock_where+' AND occurred_at<=? GROUP BY store_id,sku_id'
            stock=[dict(r) for r in db.execute(stock_query+' ORDER BY available IS NULL,store_id,sku_id LIMIT 100',[*stock_args,high.isoformat()])]
            stock_summary=dict(db.execute('SELECT COUNT(*) catalog_pairs,COUNT(available) known_pairs,SUM(available) known_units,SUM(CASE WHEN available<=? THEN 1 ELSE 0 END) low_stock_pairs FROM ('+stock_query+')',
                                          [cfg.reorder_at,*stock_args,high.isoformat()]).fetchone())
            catalog=[i for i in state(db,'catalog') if ctx.role==Role.ADMIN or i['store'] in ctx.store_ids]
            categories=sorted({i['category'] for i in catalog})
            overlay=[{'category':c,'month':m,'factor':cfg.monthly.get(c,[1]*12)[m-1]} for c in categories for m in range(1,13)]
            last=db.execute('SELECT MAX(received_at) FROM demo_events e WHERE '+where,args).fetchone()[0]
            heartbeat=state(db,'worker_heartbeat')
            status='running' if heartbeat and (now-datetime.fromisoformat(heartbeat)).total_seconds()<120 else 'worker-stopped'
            warnings=['No verified named festival calendar: missing years omit festival effects.',
                      'Baseline uses observed source days only; missing days were not treated as zero.',
                      'Copied source provenance is unverified. Generated stock and staff are simulation assumptions.']
            unused=set(cfg.monthly)-set(categories)
            if unused: warnings.append('Unmatched category weights ignored: '+', '.join(sorted(unused)))
            answer=dict(banner='SIMULATED DEMO DATA',timezone='Asia/Kolkata',source=source,start=str(start),end=str(end),
                totals=result,today=current,yesterday_elapsed=yesterday,comparison='Today to now versus the same elapsed Kolkata time yesterday; both are partial days.',
                revenue_definition='Integer paise; generated amounts after discount, before tax. Imported tax treatment unverified. Orders count distinct original sale order IDs; returns and reversals are separate signed lines.',
                daily=trends,monthly=monthly,stock=stock,stock_summary=stock_summary,stock_as_of=high.isoformat(),stock_limit=100,
                low_stock=[r for r in stock if r['available'] is not None and r['available']<=cfg.reorder_at],
                stores=sorted({i['store'] for i in catalog}),categories=categories,seasonal_overlay=overlay,
                events=[e.model_dump(mode='json') for e in cfg.events],warnings=warnings,
                last_received=last,last_success=state(db,'last_success'),next_due=state(db,'next_slot'),
                worker=status,scenario=cfg.scenario,now=now.isoformat(),
                freshness='unavailable' if not last else 'fresh' if (now-datetime.fromisoformat(last)).total_seconds()<7200 else 'stale',
                can_review_runs=ctx.role==Role.ADMIN,can_correct=ctx.role==Role.ADMIN)
        audit_operation(request.app.state.runtime,ctx,'demo.summary')
        return JSONResponse(answer,headers={'Cache-Control':'no-store'})

    @api.get('/api/demo/events')
    def events(request:Request,after:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),store:str='',sku:str='',
               category:str='',source:Literal['all','generated','imported']='all',start:date|None=None,end:date|None=None,
               known_at:datetime|None=None):
        ctx=context(request,'demo-events');where,args=clauses(ctx,store,category,source)
        now=now_utc()
        if known_at and (known_at.tzinfo is None or known_at>now): raise HTTPException(422,'Historical arrival cutoff must be timezone aware')
        if sku: where+=' AND e.sku_id=?';args.append(sku)
        if start: where+=' AND e.business_date>=?';args.append(start.isoformat())
        if end: where+=' AND e.business_date<=?';args.append(end.isoformat())
        with connect(path) as db:
            rows=[dict(r) for r in db.execute('SELECT e.rowid cursor,e.* FROM demo_events e WHERE '+where+
                ' AND e.rowid>? AND e.received_at<=? AND e.occurred_at<=? ORDER BY e.rowid LIMIT ?',
                [*args,after,(known_at or now).isoformat(),now.isoformat(),limit])]
        audit_operation(request.app.state.runtime,ctx,'demo.events')
        return JSONResponse({'rows':rows,'next':rows[-1]['cursor'] if rows else after},headers={'Cache-Control':'no-store'})

    @api.get('/api/demo/staff')
    def staff(request:Request,start:date|None=None,end:date|None=None,after:str='',limit:int=Query(50,ge=1,le=100)):
        ctx=context(request,'demo-staff')
        if ctx.role not in {Role.ADMIN,Role.HR_ADMIN,Role.HR_USER}: raise AccessDenied('HR details restricted')
        now=now_utc();today=now.astimezone(TZ).date();start=start or today;end=end or today
        if end<start or (end-start).days>800 or end>today: raise HTTPException(422,'Invalid staff date range')
        where='s.business_date BETWEEN ? AND ? AND s.id>?';args=[str(start),str(end),after]
        if ctx.role==Role.HR_USER:
            if not ctx.store_ids: raise AccessDenied('No HR stores')
            where+=' AND s.store_id IN ('+','.join('?' for _ in ctx.store_ids)+')';args+=ctx.store_ids
        with connect(path) as db:
            rows=[]
            for row in db.execute('SELECT s.*,e.payload profile FROM demo_shifts s JOIN employees e ON s.employee_id=e.employee_id WHERE '+where+' ORDER BY s.id LIMIT ?',args+[limit]):
                record=dict(row);record['profile']=json.loads(record['profile'])
                record['attendance']=[dict(r) for r in db.execute('SELECT status,occurred_at,received_at FROM demo_attendance WHERE shift_id=? AND occurred_at<=? ORDER BY occurred_at',(row['id'],now.isoformat()))]
                statuses={r['status'] for r in record['attendance']}
                record['current_status']='absent' if 'absent' in statuses else 'finished' if 'clock_out' in statuses else 'on-shift' if 'clock_in' in statuses and row['start_at']<=now.isoformat()<row['end_at'] else 'unknown'
                rows.append(record)
        audit_operation(request.app.state.runtime,ctx,'demo.staff')
        return JSONResponse({'rows':rows,'next':rows[-1]['id'] if rows else after,
            'page_summary':{s:sum(r['current_status']==s for r in rows) for s in ['absent','finished','on-shift','unknown']}},headers={'Cache-Control':'no-store'})

    @api.get('/api/demo/runs')
    def runs(request:Request,after:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100)):
        ctx=context(request,'demo-runs')
        if ctx.role!=Role.ADMIN: raise AccessDenied('Operator history restricted')
        with connect(path) as db:
            rows=[dict(r) for r in db.execute('SELECT rowid cursor,* FROM demo_runs WHERE rowid>? ORDER BY rowid LIMIT ?',(after,limit))]
        audit_operation(request.app.state.runtime,ctx,'demo.runs')
        return JSONResponse({'rows':rows,'next':rows[-1]['cursor'] if rows else after},headers={'Cache-Control':'no-store'})

    @api.post('/api/demo/correct')
    def correction(request:Request,body:Correction):
        ctx=context(request,'demo-correction')
        if ctx.role!=Role.ADMIN: raise AccessDenied('Only operators can correct demo records')
        try: result=correct(path,body.event_id,reason=body.reason,actor=ctx.principal_id,replacement_units=body.replacement_units)
        except (ValueError,sqlite3.IntegrityError): raise HTTPException(409,'Correction conflicts with retained history or stock') from None
        audit_operation(request.app.state.runtime,ctx,'demo.correct')
        return JSONResponse(result,headers={'Cache-Control':'no-store'})


import sqlite3


def inventory(path,ctx,selection):
    where,args=clauses(ctx,selection.get('store_id') or '')
    if selection.get('sku_id'): where+=' AND e.sku_id=?';args.append(selection['sku_id'])
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("SELECT store_id,sku_id,CASE WHEN SUM(CASE WHEN kind='opening' THEN 1 ELSE 0 END)>0 THEN SUM(stock_delta) ELSE NULL END available_units FROM demo_events e WHERE "+where+
            ' AND occurred_at<=? GROUP BY store_id,sku_id ORDER BY available_units IS NULL,store_id,sku_id LIMIT 100',[*args,now_utc().isoformat()])]
    return {'status':'success','summary':'SIMULATED DEMO DATA. Stock is the signed movement ledger; sales are subtracted exactly once. Unknown means no opening balance. Showing up to 100 store/SKU pairs; use Daily operations filters for drill-down.',
            'table':rows,'source':'Persistent demo movement ledger','synthetic':True}
