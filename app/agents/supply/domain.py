from datetime import date
from decimal import Decimal
from math import ceil
from statistics import mean
from typing import Annotated,Literal,Protocol
from pydantic import Field,model_validator
from app.api.schemas import Contract

class Negotiation(Contract):
    offered:Decimal=Field(gt=0)
    settled:Decimal|None=Field(default=None,gt=0)
    accepted:bool
    @model_validator(mode='after')
    def valid(self):
        if self.accepted and self.settled is None:raise ValueError('Accepted bargain needs settled price')
        return self

class Vendor(Contract):
    store_id:str=Field(min_length=1)
    vendor_id:str=Field(min_length=1)
    sku_id:str=Field(min_length=1)
    observed_on:date
    promised_lead_days:float=Field(ge=0)
    observed_lead_days:list[Annotated[float,Field(ge=0)]]=Field(default_factory=list)
    capacity:int=Field(ge=0)
    unit_cost:Decimal=Field(ge=0)
    logistics_route:str|None=None
    sop_excerpt:str|None=None
    sop_source:str|None=None
    negotiations:list[Negotiation]=Field(default_factory=list)
    source:str=Field(min_length=1)
    fixture:bool=False
    @model_validator(mode='after')
    def sop(self):
        if bool(self.sop_excerpt)!=bool(self.sop_source):raise ValueError('SOP excerpt and source must coexist')
        return self

class Query(Contract):
    store_id:str
    sku_id:str
    as_of:date
    mode:Literal['compare','replenish','sop']='compare'
    vendor_id:str|None=None
    daily_demand:float=Field(default=0,ge=0)
    stock_units:int=Field(default=0,ge=0)
    coverage_days:float=Field(default=7,ge=0,le=365)
    disruption_multiplier:float=Field(default=1,ge=1,le=10)

class StrategicPlayerModel(Protocol):
    def simulate(self,players:list[str],scenario:dict)->dict: ...

class SOPRetriever(Protocol):
    def retrieve(self,query:str,trusted_scope:str)->list[dict]: ...


def evaluate(rows:list[Vendor],query:Query)->dict:
    selected=[r for r in rows if r.store_id==query.store_id and r.sku_id==query.sku_id and r.observed_on<=query.as_of and (query.vendor_id is None or r.vendor_id==query.vendor_id)]
    if not selected:return {'status':'not_found','vendors':[]}
    keys=[(r.vendor_id,r.observed_on) for r in selected]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate vendor snapshot')
    latest={}
    for r in sorted(selected,key=lambda r:r.observed_on):latest[r.vendor_id]=r
    if query.mode=='sop':
        sources=[{'vendor_id':r.vendor_id,'excerpt':r.sop_excerpt,'source':r.sop_source,'fixture':r.fixture} for r in latest.values() if r.sop_excerpt]
        return {'status':'success' if sources else 'insufficient_evidence','sources':sources,'answer':'Supplied SOP excerpts only.' if sources else 'No SOP evidence available.'}
    required=ceil(max(0,query.daily_demand*query.coverage_days-query.stock_units))
    result=[]
    for r in latest.values():
        typical=mean(r.observed_lead_days) if r.observed_lead_days else r.promised_lead_days
        lead=typical*query.disruption_multiplier
        late=None if not r.observed_lead_days else sum(x>r.promised_lead_days for x in r.observed_lead_days)/len(r.observed_lead_days)
        completed=[n for n in r.negotiations if n.accepted]
        result.append(dict(vendor_id=r.vendor_id,source=r.source,fixture=r.fixture,lead_time_basis='observed_mean' if r.observed_lead_days else 'contract_only',
            scenario_lead_days=lead,historical_late_fraction=late,capacity=r.capacity,unit_cost=str(r.unit_cost),
            covers_required_quantity=r.capacity>=required,quantity_shortfall=max(0,required-r.capacity),
            lead_time_stockout_risk=query.stock_units<query.daily_demand*lead,logistics_route=r.logistics_route,
            bargaining_history={'accepted':len(completed),'observed':len(r.negotiations),
                'mean_settled_price':str(sum((n.settled for n in completed),Decimal(0))/len(completed)) if completed else None}))
    result.sort(key=lambda r:(not r['covers_required_quantity'],r['scenario_lead_days'],Decimal(r['unit_cost']),r['vendor_id']))
    return {'status':'success','required_quantity':required,'vendors':result,
            'recommended_vendor':next((r['vendor_id'] for r in result if r['covers_required_quantity']),None),
            'scenario_multiplier':query.disruption_multiplier,
            'warnings':['Single-vendor comparison ranks feasible capacity, then lead time, then observed unit cost.',
                        'Disruption is a supplied scenario, not a predicted event; lateness is historical frequency.',
                        'Negotiation history is descriptive; no repeated/Bayesian game solver or purchase executed.']}
