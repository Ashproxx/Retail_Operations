from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib
import json
from threading import Lock
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from app.api.schemas import Role
from app.enterprise.imports import SALES_COLUMNS, identifier, integer, number, paise
from app.enterprise.data import StoreMetadata, Product
from app.enterprise.retail import filters
from app.security.policy import AccessDenied
from app.realtime.data import SalesEvent


class Event(BaseModel):
    model_config=ConfigDict(extra='forbid')
    payload: dict
    synthetic: bool

    @field_validator('payload')
    @classmethod
    def validate_payload(cls,p):
        if set(p)!=set(SALES_COLUMNS):
            raise ValueError('Event must match Sales_Transactions columns exactly')
        for key in ('txn_id','order_id','store_id','sku_id'):identifier(p[key])
        quantity=integer(p['quantity'],1);price=number(p['unit_price_inr'],minimum=0)
        discount=number(p['discount_pct'],minimum=0,maximum=100)
        if abs(paise(p['net_amount_inr'])-paise(quantity*price*(1-discount/100)))>50:
            raise ValueError('Event money does not reconcile')
        datetime.fromisoformat(str(p['sale_date'])[:10]+'T'+str(p['sale_time']))
        for key,value in p.items():
            if isinstance(value,(dict,list)) or isinstance(value,str) and len(value)>500:
                raise ValueError('Invalid event cell')
        return p


class Ingestor:
    def __init__(self,database):self.db=database;self.lock=Lock()

    def ingest(self,event: Event,ctx, *, now=None):
        if ctx.role not in (Role.ADMIN,Role.STORE_MANAGER):
            raise AccessDenied('POS ingestion requires an administrative or store-manager grant')
        filters(ctx,{})
        payload=event.payload
        if ctx.role!=Role.ADMIN and payload['store_id'] not in ctx.store_ids:
            raise AccessDenied('Event store is outside grant')
        now=now or datetime.now(timezone.utc)
        occurred=datetime.fromisoformat(str(payload['sale_date'])[:10]+'T'+str(payload['sale_time']))
        if occurred.tzinfo is None:occurred=occurred.replace(tzinfo=ZoneInfo('Asia/Kolkata'))
        occurred=occurred.astimezone(timezone.utc)
        if occurred>now:
            raise ValueError('Future event timestamps are invalid')
        digest=hashlib.sha256(json.dumps(event.model_dump(),sort_keys=True,allow_nan=False).encode()).hexdigest()
        with self.lock,self.db.session() as session:
            if not session.get(StoreMetadata,payload['store_id']) or not session.get(Product,payload['sku_id']):
                raise ValueError('Unknown store or product')
            prior=session.scalar(select(SalesEvent).where(SalesEvent.txn_id==payload['txn_id']))
            if prior:
                if prior.digest!=digest:raise ValueError('Transaction ID conflicts with an existing event')
                return {'status':'duplicate','id':prior.id}
            row=SalesEvent(txn_id=payload['txn_id'],store_id=payload['store_id'],occurred_at=occurred.isoformat(),received_at=now.isoformat(),
                           quantity=int(payload['quantity']),synthetic=event.synthetic,source='synthetic-stream' if event.synthetic else 'pos-webhook',digest=digest,payload=payload)
            session.add(row);session.flush();return {'status':'inserted','id':row.id}
