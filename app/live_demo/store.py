"""One append-only event ledger and one sales-fact projection, committed atomically."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib
import sqlite3
import uuid
from app.live_demo.config import UTC, TZ, Config, digest, instant


def now_utc(): return datetime.now(UTC)


@contextmanager
def connect(path,*,write=False):
    db=sqlite3.connect(f'file:{Path(path).resolve().as_posix()}?mode=rw',uri=True,timeout=2)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        if write: db.execute('BEGIN IMMEDIATE')
        yield db
        if write: db.commit()
    except BaseException:
        db.rollback();raise
    finally: db.close()


def state(db,key):
    row=db.execute('SELECT value FROM demo_state WHERE key=?',(key,)).fetchone()
    if row is None: raise ValueError('Initialize a dedicated demo database first')
    return json.loads(row[0])


def set_state(db,key,value):
    db.execute('INSERT INTO demo_state VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
               (key,json.dumps(value,sort_keys=True)))


def new_run(db,source,checksum,now):
    identity=uuid.uuid4().hex
    db.execute('INSERT INTO demo_runs(id,source,checksum,started_at,status) VALUES(?,?,?,?,?)',
               (identity,source,checksum,now.isoformat(),'running'))
    return identity


def balance(db,store,sku,at=None):
    at=at or now_utc().isoformat()
    row=db.execute("SELECT COUNT(CASE WHEN kind='opening' THEN 1 END),SUM(stock_delta) FROM demo_events WHERE store_id=? AND sku_id=? AND occurred_at<=?",
                   (store,sku,at)).fetchone()
    return row[1] if row[0] else None


def append(db,*,run_id,source,identity,store,sku,kind,quantity,unit=0,discount=0,net=0,
           stock=None,at,received,order=None,original=None,reason=None,actor='local-worker',factors=None,synthetic=1):
    if at.tzinfo is None or received.tzinfo is None or at>received: raise ValueError('Invalid or future instant')
    if any(type(x) is not int for x in [quantity,unit,discount,net]) or unit<0 or not 0<=discount<=10000:
        raise ValueError('Invalid quantity or money')
    if stock is not None and type(stock) is not int: raise ValueError('Invalid stock movement')
    if kind not in {'opening','delivery','sale','return','damaged_return','adjustment','reversal','lost','imported'}:
        raise ValueError('Unknown event kind')
    if kind in {'opening','delivery','sale','lost'} and quantity<=0: raise ValueError('Positive quantity required')
    if kind in {'delivery','adjustment'} and (stock!=quantity or net!=0): raise ValueError('Movement does not reconcile')
    if kind=='adjustment' and (not reason or not actor): raise ValueError('Adjustment requires a reason and actor')
    body=dict(source=source,source_record_id=identity,store_id=store,sku_id=sku,kind=kind,order_id=order,
        quantity=quantity,unit_paise=unit,discount_bps=discount,net_paise=net,stock_delta=stock,
        occurred_at=at.astimezone(UTC).isoformat(),business_date=at.astimezone(TZ).date().isoformat(),
        synthetic=synthetic,original_id=original,reason=reason,actor=actor,factors=json.dumps(factors or {},sort_keys=True))
    fingerprint=digest(body)
    previous=db.execute('SELECT id,digest FROM demo_events WHERE source=? AND source_record_id=?',(source,identity)).fetchone()
    if previous:
        if previous['digest']!=fingerprint: raise ValueError('Same identity has conflicting content')
        return previous['id'],False
    event_id=digest([source,identity])
    if kind=='opening':
        if balance(db,store,sku,body['occurred_at']) is not None: raise ValueError('Opening balance already exists')
        if stock!=quantity: raise ValueError('Opening stock mismatch')
    elif stock is not None:
        available=balance(db,store,sku,body['occurred_at'])
        if available is None: raise ValueError('Stock coverage is unknown')
        if available+stock<0: raise ValueError('Insufficient available stock')
        # Late corrections must not create a negative balance at any later movement boundary.
        running=available+stock
        for row in db.execute('SELECT stock_delta FROM demo_events WHERE store_id=? AND sku_id=? AND occurred_at>? ORDER BY occurred_at,id',
                              (store,sku,body['occurred_at'])):
            running+=row[0] or 0
            if running<0: raise ValueError('Correction would oversell later stock')
    if kind=='sale' and (stock!=-quantity or net!=(quantity*unit*(10000-discount)+5000)//10000):
        raise ValueError('Sale does not reconcile')
    if kind in {'return','damaged_return'}:
        sold=db.execute("SELECT * FROM demo_events WHERE id=? AND kind='sale'",(original,)).fetchone()
        if not sold or sold['store_id']!=store or sold['sku_id']!=sku or quantity>=0 or body['occurred_at']<sold['occurred_at']:
            raise ValueError('Invalid return reference')
        if db.execute("SELECT 1 FROM demo_events WHERE original_id=? AND kind='reversal'",(original,)).fetchone():
            raise ValueError('Sale already reversed')
        returned=db.execute("SELECT COALESCE(-SUM(quantity),0) FROM demo_events WHERE original_id=? AND kind IN('return','damaged_return')",(original,)).fetchone()[0]
        if returned-quantity>sold['quantity']: raise ValueError('Return exceeds sold units')
        if stock!=(-quantity if kind=='return' else 0) or net!=-((-quantity*sold['net_paise'])//sold['quantity']):
            raise ValueError('Return money or stock mismatch')
    if kind=='reversal':
        prior=db.execute("SELECT * FROM demo_events WHERE id=? AND kind IN('sale','adjustment')",(original,)).fetchone()
        if not prior or not reason or not actor: raise ValueError('Correction requires original, reason and actor')
        if any(body[k]!=prior[k] for k in ['store_id','sku_id','occurred_at']): raise ValueError('Reversal identity mismatch')
        if (quantity,net,stock)!=(-prior['quantity'],-prior['net_paise'],-prior['stock_delta']): raise ValueError('Reversal mismatch')
        if db.execute('SELECT 1 FROM demo_events WHERE original_id=?',(original,)).fetchone(): raise ValueError('Original already returned or corrected')
    body.update(id=event_id,digest=fingerprint,run_id=run_id,received_at=received.astimezone(UTC).isoformat())
    db.execute('INSERT INTO demo_events('+','.join(body)+') VALUES('+','.join('?' for _ in body)+')',tuple(body.values()))
    if kind in {'sale','return','damaged_return'} or kind=='reversal' and prior['kind']=='sale':
        product=json.loads(db.execute('SELECT payload FROM retail_products WHERE sku_id=?',(sku,)).fetchone()[0])
        category=product.get('normalized_category') or product.get('category') or 'Unknown'
        payload={**product,**body,'sale_date':body['business_date'],'sale_time':at.astimezone(TZ).time().isoformat(),
                 'unit_price_inr':unit/100,'discount_pct':discount/100,'net_amount_inr':net/100}
        db.execute('INSERT INTO sales_transactions VALUES(?,?,?,?,?,?,?,?,?,?)',
                   (event_id,order or event_id,store,sku,body['business_date'],category,'Simulated store',quantity,net,json.dumps(payload)))
    return event_id,True


def initialize(path,source=None,config=None,now=None):
    from app.models.database import Base
    from app.services.database_service import Database
    from app.enterprise.data import Sale, Product
    from app.employees.data import Employee
    from app.integration.repository import StoreRow
    # Register the website's observation table before workers can acquire write locks.
    from app.conversation.catalog import ObservationRow
    now=now or now_utc();path=Path(path).resolve();config=config or Config()
    if source and path==Path(source).resolve(): raise ValueError('Demo must be separate from source')
    if path.exists():
        with connect(path) as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='demo_schema'").fetchone():
                raise ValueError('Refusing to initialize a populated non-demo database')
            if db.execute("SELECT 1 FROM demo_state WHERE key='config'").fetchone():
                saved=state(db,'config')
                if saved['version']!=config.version or saved['scenario']!=config.scenario: raise ValueError('Existing scenario differs')
                return {'status':'already_initialized','config':saved}
    path.parent.mkdir(parents=True,exist_ok=True)
    database=Database('sqlite:///'+path.as_posix())
    Base.metadata.create_all(database.engine);database.close()
    with connect(path) as db: db.executescript(Path(__file__).with_name('schema.sql').read_text())
    snapshot=None
    try:
        if source:
            snapshot=sqlite3.connect(':memory:');snapshot.row_factory=sqlite3.Row
            with sqlite3.connect(f'file:{Path(source).resolve().as_posix()}?mode=ro',uri=True) as original:
                original.backup(snapshot)
        with connect(path,write=True) as db:
            config=config.model_copy(update={'start_date':config.start_date or now.astimezone(TZ).date()-timedelta(days=7)})
            run=new_run(db,'bootstrap',digest(config.model_dump(mode='json')),now)
            count=0;lo=None;hi=None;source_checksum=hashlib.sha256()
            if snapshot:
                # Whitelist only catalog, store and sales facts. Never copy sessions, credentials or staff records.
                for row in snapshot.execute('SELECT id,name FROM stores ORDER BY id'):
                    db.execute('INSERT INTO stores VALUES(?,?)',tuple(row))
                for row in snapshot.execute('SELECT sku_id,payload FROM retail_products ORDER BY sku_id'):
                    payload=json.loads(row['payload']); safe={k:payload[k] for k in ['category','normalized_category','style_name','gender','color','size'] if k in payload}
                    db.execute('INSERT INTO retail_products VALUES(?,?)',(row['sku_id'],json.dumps(safe)))
                for row in snapshot.execute('SELECT * FROM sales_transactions ORDER BY day,txn_id'):
                    if row['quantity']<=0 or row['net_paise']<0: raise ValueError('Source contains corrections; use a reviewed export')
                    raw=json.loads(row['payload']); stamp=raw.get('sale_time','12:00:00')
                    try: at=datetime.fromisoformat(row['day']+'T'+str(stamp)).replace(tzinfo=TZ).astimezone(UTC)
                    except ValueError: raise ValueError('Source transaction has invalid time') from None
                    if at>now: raise ValueError('Source contains future completed sales')
                    safe={k:raw[k] for k in ['style_name','gender','color','size','unit_price_inr','discount_pct','sale_time'] if k in raw}
                    safe.update(source='copied-unverified',synthetic=None,source_record_id=row['txn_id'],received_at=now.isoformat())
                    values=[row[k] for k in ['txn_id','order_id','store_id','sku_id','day','category','channel','quantity','net_paise']]+[json.dumps(safe)]
                    source_checksum.update(json.dumps(values[:-1],separators=(',',':')).encode())
                    db.execute('INSERT INTO sales_transactions VALUES(?,?,?,?,?,?,?,?,?,?)',values)
                    append(db,run_id=run,source='copied-unverified',identity=row['txn_id'],store=row['store_id'],sku=row['sku_id'],
                           kind='imported',quantity=row['quantity'],net=row['net_paise'],at=at,received=now,
                           order=row['order_id'],unit=round(float(raw.get('unit_price_inr',0))*100),
                           discount=round(float(raw.get('discount_pct',0))*100),synthetic=None)
                    lo=min(lo or row['day'],row['day']);hi=max(hi or row['day'],row['day']);count+=1
            if not db.execute('SELECT 1 FROM stores').fetchone():
                db.execute("INSERT INTO stores VALUES('DEMO1','Demo store')")
                db.execute('INSERT INTO retail_products VALUES(?,?)',('DEMO-SKU',json.dumps({'category':'Unknown','style_name':'Demo item'})))
            catalog=[]
            for store in db.execute('SELECT id FROM stores ORDER BY id LIMIT ?',(config.max_stores,)).fetchall():
                items=db.execute('WITH rates AS (SELECT sku_id,category,AVG(net_paise*1.0/quantity) price,SUM(quantity)*1.0/COUNT(DISTINCT day)/10 rate FROM sales_transactions WHERE store_id=? GROUP BY sku_id), ranked AS (SELECT *,ROW_NUMBER() OVER(PARTITION BY category ORDER BY sku_id) n FROM rates) SELECT sku_id,price,rate FROM ranked ORDER BY n,category,sku_id LIMIT ?',
                                 (store[0],config.products_per_store)).fetchall()
                if not items: items=[(r[0],10000,.5) for r in db.execute('SELECT sku_id FROM retail_products ORDER BY sku_id LIMIT ?',(config.products_per_store,))]
                for sku,price,rate in items:
                    payload=json.loads(db.execute('SELECT payload FROM retail_products WHERE sku_id=?',(sku,)).fetchone()[0])
                    catalog.append(dict(store=store[0],sku=sku,unit=max(100,min(1000000,round(price))),rate=max(.1,min(2,rate)),
                                        category=payload.get('normalized_category') or payload.get('category') or 'Unknown'))
                for n in range(3):
                    employee=f'DEMO-{store[0]}-{n+1}'
                    payload={'employee_id':employee,'full_name':f'Demo colleague {store[0]} {n+1}','store_id':store[0],
                             'employment_status':'Active','department':'Retail','designation':'Demo associate','shift':'10:00-18:00',
                             'source':'synthetic-demo','synthetic':True,'effective_from':config.start_date.isoformat()}
                    db.execute('INSERT INTO employees VALUES(?,?,?,?)',(employee,store[0],payload['full_name'].lower(),json.dumps(payload)))
            set_state(db,'config',config.model_dump(mode='json'));set_state(db,'catalog',catalog)
            set_state(db,'imported_range',[lo,hi]);set_state(db,'next_slot',instant(config.start_date,10).isoformat())
            set_state(db,'last_success',None);set_state(db,'worker_heartbeat',None)
            db.execute("UPDATE demo_runs SET ended_at=?,status='success',accepted=?,checksum=? WHERE id=?",(now.isoformat(),count,source_checksum.hexdigest(),run))
            return {'status':'initialized','imported_sales':count,'generated_catalog_pairs':len(catalog)}
    except Exception as exc:
        with connect(path,write=True) as db:
            run=new_run(db,'bootstrap-failed','',now)
            db.execute("UPDATE demo_runs SET ended_at=?,status='failed',rejected=1,error=? WHERE id=?",(now.isoformat(),str(exc)[:200],run))
        raise
    finally:
        if snapshot: snapshot.close()
