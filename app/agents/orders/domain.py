from decimal import Decimal
from typing import Literal,Protocol
from pydantic import Field,AwareDatetime,model_validator
from app.api.schemas import Contract
State=Literal['created','packed','shipped','delivered','cancelled']
TRANSITIONS={'created':{'packed','cancelled'},'packed':{'shipped','cancelled'},'shipped':{'delivered'},'delivered':set(),'cancelled':set()}

def validate_transition(old:State,new:State)->None:
    if new not in TRANSITIONS.get(old,set()):raise ValueError('Invalid fulfillment transition')

class Source(Contract):
    source_id:str=Field(min_length=1)
    capacity:int=Field(ge=0)
    unit_fulfillment_cost:Decimal=Field(ge=0)
    arrival_at:AwareDatetime

class Order(Contract):
    store_id:str=Field(min_length=1)
    order_id:str=Field(min_length=1)
    sku_id:str=Field(min_length=1)
    quantity:int=Field(gt=0)
    state:State
    placed_at:AwareDatetime
    updated_at:AwareDatetime
    promised_at:AwareDatetime
    shipped_at:AwareDatetime|None=None
    delivered_at:AwareDatetime|None=None
    estimated_arrival:AwareDatetime|None=None
    tracking_reference:str|None=None
    fulfillment_sources:list[Source]=Field(default_factory=list)
    source:str=Field(min_length=1)
    fixture:bool=False
    @model_validator(mode='after')
    def timeline(self):
        if self.updated_at<self.placed_at or self.promised_at<self.placed_at:raise ValueError('Invalid order timeline')
        for event in [self.shipped_at,self.delivered_at]:
            if event and not self.placed_at<=event<=self.updated_at:raise ValueError('Invalid event time')
        if self.state=='delivered' and self.delivered_at is None:raise ValueError('Delivery time required')
        if self.state=='shipped' and self.shipped_at is None:raise ValueError('Shipping time required')
        if self.shipped_at and self.state not in {'shipped','delivered'}:raise ValueError('Shipping state mismatch')
        if self.estimated_arrival and self.estimated_arrival<self.placed_at:raise ValueError('ETA precedes order')
        if self.delivered_at and self.state!='delivered':raise ValueError('Delivery state mismatch')
        if self.shipped_at and self.delivered_at and self.shipped_at>self.delivered_at:raise ValueError('Delivery precedes shipping')
        ids=[s.source_id for s in self.fulfillment_sources]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate fulfillment source')
        return self

class Query(Contract):
    store_id:str
    order_id:str
    as_of:AwareDatetime
    mode:Literal['status','allocation']='status'

class ShippingConnector(Protocol):
    def latest(self,order_id:str)->Order|None: ...


def evaluate(rows:list[Order],query:Query)->dict:
    found=[r for r in rows if r.store_id==query.store_id and r.order_id==query.order_id and r.updated_at<=query.as_of]
    if not found:return {'status':'not_found','order':None}
    if len({r.updated_at for r in found})!=len(found):raise ValueError('Duplicate order snapshot')
    r=max(found,key=lambda r:r.updated_at)
    if query.mode=='allocation':
        if r.state not in {'created','packed'}:return {'status':'insufficient_evidence','reason':'Order is no longer awaiting allocation.'}
        remaining=r.quantity;allocations=[];cost=Decimal(0)
        for s in sorted(r.fulfillment_sources,key=lambda s:(s.unit_fulfillment_cost,s.arrival_at,s.source_id)):
            if not query.as_of<=s.arrival_at<=r.promised_at:continue
            qty=min(remaining,s.capacity)
            if qty:allocations.append({'source_id':s.source_id,'quantity':qty});cost+=qty*s.unit_fulfillment_cost;remaining-=qty
            if not remaining:break
        return {'status':'success' if not remaining else 'insufficient_evidence','allocations':allocations,
                'unallocated_quantity':remaining,'total_variable_cost':str(cost),'split_shipment':len(allocations)>1,
                'source':r.source,'fixture':r.fixture,'operational_write_performed':False,
                'assumptions':['Single SKU, divisible quantity, known independent capacities, additive unit costs, no fixed shipping fees.']}
    if r.state=='cancelled':sla='not_applicable';late=False
    elif r.state=='delivered':sla='late' if r.delivered_at>r.promised_at else 'on_time';late=sla=='late'
    else:sla='overdue' if query.as_of>r.promised_at else 'pending';late=sla=='overdue' or bool(r.estimated_arrival and r.estimated_arrival>r.promised_at)
    return {'status':'success','order':r.model_dump(mode='json'),'sla':sla,'delay_risk':late,
            'overdue_hours':max(0,((r.delivered_at or query.as_of)-r.promised_at).total_seconds()/3600) if r.state!='cancelled' else 0,
            'prediction_basis':'observed status, promised deadline and supplied ETA; no trained delay predictor'}
