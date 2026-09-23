from datetime import date
from decimal import Decimal,ROUND_DOWN
from typing import Literal,Protocol
import re
from pydantic import Field,model_validator
from app.api.schemas import Contract
Reason=Literal['defect','wrong_item','change_of_mind','other']

class Policy(Contract):
    window_days:int=Field(ge=0,le=3650)
    allowed_reasons:list[Reason]
    receipt_required:bool
    allow_opened:bool
    source:str=Field(min_length=1)

class ReturnRecord(Contract):
    store_id:str=Field(min_length=1)
    order_id:str=Field(min_length=1)
    observed_on:date
    delivered_on:date|None=None
    purchased_units:int=Field(gt=0)
    previously_returned_units:int=Field(default=0,ge=0)
    paid_total:Decimal=Field(ge=0,decimal_places=2)
    refunded_total:Decimal=Field(default=Decimal(0),ge=0,decimal_places=2)
    refund_status:Literal['requested','approved','paid','rejected']|None=None
    policy:Policy|None=None
    prior_return_count:int|None=Field(default=None,ge=0)
    source:str=Field(min_length=1)
    fixture:bool=False
    @model_validator(mode='after')
    def totals(self):
        if self.previously_returned_units>self.purchased_units:raise ValueError('Returned quantity exceeds purchase')
        if self.refunded_total>self.paid_total:raise ValueError('Refund total exceeds payment')
        if self.delivered_on and self.delivered_on>self.observed_on:raise ValueError('Observed delivery is in future')
        return self

class Query(Contract):
    store_id:str
    order_id:str
    as_of:date
    mode:Literal['eligibility','refund_status']='eligibility'
    units_requested:int=Field(default=1,gt=0)
    reason:Reason='other'
    has_receipt:bool=False
    opened:bool=False
    serial_mismatch:bool=False
    review_count_threshold:int=Field(default=5,ge=1)

class FraudRiskModel(Protocol):
    def assess(self,features:dict)->dict: ...

class RefundConnector(Protocol):
    def lookup(self,order_id:str)->ReturnRecord|None: ...


def categorize_reason(text:str)->Reason:
    text=text.lower()
    for reason,pattern in [('wrong_item',r'wrong (?:item|size|colour|color)'),('defect',r'\b(?:broken|defect\w*|damaged)\b'),('change_of_mind',r'changed? (?:my )?mind|no longer want')]:
        if re.search(pattern,text):return reason
    return 'other'


def evaluate(rows:list[ReturnRecord],query:Query)->dict:
    rows=[r for r in rows if r.store_id==query.store_id and r.order_id==query.order_id and r.observed_on<=query.as_of]
    if not rows:return {'status':'not_found','result':None}
    if len({r.observed_on for r in rows})!=len(rows):raise ValueError('Duplicate return snapshot')
    r=max(rows,key=lambda r:r.observed_on)
    if query.mode=='refund_status':
        return {'status':'success' if r.refund_status else 'insufficient_evidence','refund_status':r.refund_status,
                'recorded_refunded_total':str(r.refunded_total),'source':r.source,'fixture':r.fixture}
    if r.policy is None:return {'status':'insufficient_evidence','eligible':None,'reason':'No supplied return policy.'}
    reasons=[]
    if r.delivered_on is None:reasons.append('delivery_not_recorded')
    elif (query.as_of-r.delivered_on).days>r.policy.window_days:reasons.append('outside_supplied_window')
    if query.units_requested>r.purchased_units-r.previously_returned_units:reasons.append('quantity_exceeds_remaining_purchase')
    if query.reason not in r.policy.allowed_reasons:reasons.append('reason_not_allowed')
    if r.policy.receipt_required and not query.has_receipt:reasons.append('receipt_required')
    if query.opened and not r.policy.allow_opened:reasons.append('opened_not_allowed')
    flags=[]
    if query.serial_mismatch:flags.append('reported_serial_mismatch')
    if r.prior_return_count is not None and r.prior_return_count>=query.review_count_threshold:flags.append('return_count_review_threshold')
    eligible=not reasons
    amount=(min(r.paid_total-r.refunded_total,r.paid_total/r.purchased_units*query.units_requested)).quantize(Decimal('.01'),rounding=ROUND_DOWN) if eligible else None
    return {'status':'success','eligible':eligible,'ineligibility_reasons':reasons,'reason_category':query.reason,
            'advisory_refund_amount':str(amount) if amount is not None else None,'risk_review_flags':flags,
            'requires_human':bool(flags),'source':r.source,'policy_source':r.policy.source,'fixture':r.fixture,
            'refund_executed':False,'warnings':['Policy is supplied evidence, not a legal entitlement decision.',
            'Refund estimate uses equal per-unit allocation of recorded payment; actual taxes/fees need integration.',
            'Risk flags are uncalibrated review rules, not a fraud finding.']}
