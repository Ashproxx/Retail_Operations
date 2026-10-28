from datetime import date, datetime, timedelta
import json
import sqlite3
from app.live_demo.config import Config, TZ, UTC, digest, factors, instant, next_slot, rng, sample
from app.live_demo.store import append, balance, connect, new_run, now_utc, set_state, state


def process_slot(db,slot,config,catalog,run,received):
    day=slot.astimezone(TZ).date();hour=slot.astimezone(TZ).hour
    imported=state(db,'imported_range')
    if imported[0] and imported[0]<=day.isoformat()<=imported[1]: return 0
    source='simulated:'+config.scenario;count=0
    def event(item,kind,identity,qty,**kwargs):
        nonlocal count
        result=append(db,run_id=run,source=source,identity=identity,store=item['store'],sku=item['sku'],
                      kind=kind,quantity=qty,at=slot,received=received,**kwargs)
        count+=result[1];return result[0]
    for item in catalog:
        store,sku=item['store'],item['sku'];key=f'{slot.isoformat()}:{store}:{sku}'
        randomizer=rng(config,key);weights=factors(config,day,item['category'])
        if balance(db,store,sku,slot.isoformat()) is None:
            event(item,'opening','opening:'+store+':'+sku,config.opening_units,stock=config.opening_units,
                  reason='Synthetic opening assumption, not imported stock')
        for order in db.execute('SELECT * FROM demo_orders WHERE store_id=? AND sku_id=? AND due_at<=? AND delivered_at IS NULL ORDER BY id',
                                (store,sku,slot.isoformat())).fetchall():
            event(item,'delivery','delivery:'+order['id'],order['quantity'],stock=order['quantity'])
            db.execute('UPDATE demo_orders SET delivered_at=? WHERE id=?',(slot.isoformat(),order['id']))
        demand=sample(config,item['rate']*weights['combined'],randomizer)
        available=balance(db,store,sku,slot.isoformat());fulfilled=min(available,demand)
        weights.update(baseline_per_observed_hour=item['rate'],requested_units=demand)
        if fulfilled:
            event(item,'sale',key,fulfilled,unit=item['unit'],discount=config.discount_bps,
                  net=(fulfilled*item['unit']*(10000-config.discount_bps)+5000)//10000,stock=-fulfilled,
                  order=digest([config.scenario,slot.isoformat(),store,int(randomizer.random()*3)]),factors=weights)
        if demand>fulfilled: event(item,'lost',key+':lost',demand-fulfilled,stock=0,factors=weights)
        if hour==18 and randomizer.random()<.15:
            sold=db.execute("SELECT s.* FROM demo_events s WHERE s.store_id=? AND s.sku_id=? AND s.kind='sale' AND s.occurred_at<? AND NOT EXISTS(SELECT 1 FROM demo_events r WHERE r.original_id=s.id) ORDER BY s.occurred_at DESC,s.id LIMIT 1",
                            (store,sku,instant(day,0).isoformat())).fetchone()
            if sold:
                damaged=randomizer.random()<.2
                event(item,'damaged_return' if damaged else 'return',key+':return',-1,
                      net=-(sold['net_paise']//sold['quantity']),stock=0 if damaged else 1,
                      original=sold['id'],reason='Simulated damaged quarantine' if damaged else 'Simulated sellable return')
        if balance(db,store,sku,slot.isoformat())<=config.reorder_at and not db.execute(
                'SELECT 1 FROM demo_orders WHERE store_id=? AND sku_id=? AND delivered_at IS NULL',(store,sku)).fetchone():
            db.execute('INSERT INTO demo_orders VALUES(?,?,?,?,?,?,NULL)',
                       (digest([key,'replenishment']),store,sku,slot.isoformat(),instant(day+timedelta(days=config.lead_days),10).isoformat(),config.delivery_units))
    for employee in db.execute('SELECT employee_id,store_id FROM employees ORDER BY employee_id').fetchall():
        eid,store=employee;shift_id=digest([config.scenario,eid,day.isoformat()])
        if day.weekday()==rng(config,eid,'weekly-off').randrange(7): continue
        start=instant(day,10);end=instant(day,18)
        db.execute('INSERT OR IGNORE INTO demo_shifts(id,employee_id,store_id,business_date,start_at,end_at) VALUES(?,?,?,?,?,?)',
                   (shift_id,eid,store,day.isoformat(),start.isoformat(),end.isoformat()))
        absent=rng(config,eid,day.isoformat(),'attendance').random()<.06
        states=[('absent' if absent else 'clock_in',start)]
        if not absent and end<=slot: states.append(('clock_out',end))
        for status,at in states:
            if at<=received:
                db.execute('INSERT OR IGNORE INTO demo_attendance VALUES(?,?,?,?,?)',
                           (digest([shift_id,status]),shift_id,status,at.isoformat(),received.isoformat()))
    return count


def run_once(path,*,through=None,now=None,max_slots=100,crash_after=None):
    now=now or now_utc()
    if not 1<=max_slots<=1000: raise ValueError('Batch must contain 1 to 1000 slots')
    limit=min(now,instant(through+timedelta(days=1),0)-timedelta(microseconds=1)) if through else now
    if through and through>now.astimezone(TZ).date(): raise ValueError('Future business date is not completed')
    with connect(path,write=True) as db:
        config=Config.model_validate(state(db,'config'));catalog=state(db,'catalog')
        db.execute("UPDATE demo_runs SET status='interrupted',ended_at=?,error='No completion recorded within one hour; committed slots retained' WHERE status='running' AND started_at<?",
                   (now.isoformat(),(now-timedelta(hours=1)).isoformat()))
        run=new_run(db,'generator',digest(config.model_dump(mode='json')),now)
    accepted=0;slots=0
    try:
        while slots<max_slots:
            # SQLite BEGIN IMMEDIATE serializes all writers, including independent processes.
            with connect(path,write=True) as db:
                slot=datetime.fromisoformat(state(db,'next_slot'))
                if slot>limit: break
                count=process_slot(db,slot,config,catalog,run,now)
                if crash_after is not None and slots==crash_after: raise RuntimeError('Injected crash before checkpoint')
                db.execute('INSERT INTO demo_checkpoints VALUES(?,?,?)',(slot.isoformat(),run,now.isoformat()))
                set_state(db,'next_slot',next_slot(slot).isoformat());set_state(db,'last_success',now.isoformat())
                db.execute('UPDATE demo_runs SET accepted=accepted+? WHERE id=?',(count,run))
            accepted+=count;slots+=1
        with connect(path,write=True) as db:
            db.execute("UPDATE demo_runs SET ended_at=?,status='success',skipped=? WHERE id=?",(now.isoformat(),int(slots==0),run))
        return {'run_id':run,'accepted':accepted,'slots':slots,'status':'success'}
    except Exception as exc:
        with connect(path,write=True) as db:
            db.execute("UPDATE demo_runs SET ended_at=?,status='failed',rejected=1,error=? WHERE id=?",(now.isoformat(),str(exc)[:200],run))
        raise


def correct(path,event_id,*,reason,actor,replacement_units=None,now=None):
    now=now or now_utc()
    if not reason.strip() or not actor.strip(): raise ValueError('Reason and actor required')
    with connect(path,write=True) as db: run=new_run(db,'correction',digest([event_id,reason,actor,replacement_units]),now)
    try:
        with connect(path,write=True) as db:
            original=db.execute("SELECT * FROM demo_events WHERE id=? AND kind='sale'",(event_id,)).fetchone()
            if not original: raise ValueError('Only generated sales can be corrected here')
            reversal=db.execute("SELECT 1 FROM demo_events WHERE original_id=? AND kind='reversal'",(event_id,)).fetchone()
            replacement=db.execute("SELECT 1 FROM demo_events WHERE original_id=? AND kind='sale'",(event_id,)).fetchone()
            if reversal and bool(replacement)!=(replacement_units is not None):
                raise ValueError('Existing correction has different replacement content')
            kwargs=dict(run_id=run,source='correction',store=original['store_id'],sku=original['sku_id'],
                        at=datetime.fromisoformat(original['occurred_at']),received=now,original=event_id,reason=reason,actor=actor)
            _,inserted=append(db,identity='reverse:'+event_id,kind='reversal',quantity=-original['quantity'],net=-original['net_paise'],
                   stock=-original['stock_delta'],**kwargs)
            accepted=int(inserted);skipped=int(not inserted)
            if replacement_units is not None:
                if type(replacement_units) is not int or replacement_units<=0: raise ValueError('Replacement units must be positive')
                _,inserted=append(db,identity='replace:'+event_id,kind='sale',quantity=replacement_units,
                       unit=original['unit_paise'],discount=original['discount_bps'],
                       net=(replacement_units*original['unit_paise']*(10000-original['discount_bps'])+5000)//10000,
                       stock=-replacement_units,order='replacement:'+event_id,**kwargs)
                accepted+=int(inserted);skipped+=int(not inserted)
            db.execute("UPDATE demo_runs SET ended_at=?,status='success',accepted=?,skipped=? WHERE id=?",
                       (now.isoformat(),accepted,skipped,run))
            return {'run_id':run,'original_retained':event_id}
    except Exception as exc:
        with connect(path,write=True) as db:
            db.execute("UPDATE demo_runs SET ended_at=?,status='failed',rejected=1,error=? WHERE id=?",(now.isoformat(),str(exc)[:200],run))
        raise
