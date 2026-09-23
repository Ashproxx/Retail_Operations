from datetime import date
from decimal import Decimal
from collections import defaultdict
from statistics import mean
from typing import Protocol
from pydantic import Field,model_validator
from app.api.schemas import Contract,AuditEvent

class Sale(Contract):
    store_id:str=Field(min_length=1)
    sku_id:str=Field(min_length=1)
    category:str=Field(min_length=1)
    day:date
    units_sold:int=Field(ge=0)
    unit_price_inr:Decimal=Field(ge=0)
    closing_stock:int=Field(ge=0)
    reorder_point:int=Field(ge=0)
    stockout_risk_flag:bool | None=None
    source:str=Field(min_length=1)
    fixture:bool=False

class Query(Contract):
    start:date
    end:date
    store_id:str|None=None
    sku_id:str|None=None
    top_n:int=Field(default=5,ge=1,le=100)
    @model_validator(mode='after')
    def dates(self):
        if self.end<self.start:raise ValueError('Reversed date range')
        return self

class AnomalyDetector(Protocol):
    def detect(self,metrics:list[float])->list[int]: ...


def agent_metrics(events:list[AuditEvent])->dict:
    by_agent=defaultdict(list)
    for event in events:
        for agent in set(event.agents_called):by_agent[agent].append(event)
    return {agent:{'requests':len(rows),'average_request_latency_ms':mean(r.latency_ms for r in rows),
        'error_requests':sum(r.final_status=='error' for r in rows),
        'escalated_requests':sum(r.final_status=='escalated' for r in rows),
        'note':'Request latency includes all agents; not isolated agent runtime or prediction accuracy.'} for agent,rows in by_agent.items()}


def evaluate(rows:list[Sale],query:Query)->dict:
    rows=[r for r in rows if query.start<=r.day<=query.end and (query.store_id is None or r.store_id==query.store_id)
          and (query.sku_id is None or r.sku_id==query.sku_id)]
    if not rows:return {'status':'not_found','summary':{}}
    keys=[(r.store_id,r.sku_id,r.day) for r in rows]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate daily store/SKU aggregate')
    by_store=defaultdict(lambda:Decimal(0));by_category=defaultdict(lambda:Decimal(0));by_sku=defaultdict(int)
    by_day=defaultdict(int);latest={}
    for r in rows:
        revenue=r.unit_price_inr*r.units_sold
        by_store[r.store_id]+=revenue;by_category[r.category]+=revenue;by_sku[r.sku_id]+=r.units_sold
        by_day[r.day]+=r.closing_stock
        key=(r.store_id,r.sku_id)
        if key not in latest or r.day>latest[key].day:latest[key]=r
    observed=mean(by_day.values());total_units=sum(by_sku.values())
    ranking=sorted(by_sku.items(),key=lambda x:(-x[1],x[0]))
    return {'status':'success','summary':{'units_sold':total_units,'sales_inr':str(sum(by_store.values())),
            'low_stock_count':sum(r.closing_stock<r.reorder_point for r in latest.values()),
            'stockout_count':sum(r.closing_stock==0 for r in latest.values()),
            'stockout_risk_count':sum(r.stockout_risk_flag is True for r in latest.values()),
            'unknown_risk_count':sum(r.stockout_risk_flag is None for r in latest.values()),
            'inventory_turnover_proxy':None if observed==0 else total_units/observed},
            'sales_by_store':{k:str(v) for k,v in sorted(by_store.items())},
            'sales_by_category':{k:str(v) for k,v in sorted(by_category.items())},
            'top_skus':ranking[:query.top_n],
            'slow_moving_skus':sorted(by_sku.items(),key=lambda x:(x[1],x[0]))[:query.top_n],
            'snapshot_dates':{s+'/'+k:r.day.isoformat() for (s,k),r in latest.items()},
            'sources':sorted({r.source for r in rows}),
            'warnings':['Revenue is units times observed unit price; no tax/discount/refund adjustment inferred.',
                        'Turnover proxy uses mean observed daily closing-stock totals, not financial cost-of-goods turnover.',
                        'Latest stock is per SKU/store; dates may differ and missing days/SKUs are not imputed.']}
