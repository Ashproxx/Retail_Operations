from datetime import date
from decimal import Decimal,ROUND_CEILING,ROUND_HALF_UP,ROUND_FLOOR
from typing import Literal,Protocol
from pydantic import Field,model_validator
from app.api.schemas import Contract

class Price(Contract):
    store_id:str=Field(min_length=1)
    sku_id:str=Field(min_length=1)
    observed_on:date
    current_price:Decimal=Field(gt=0,decimal_places=2)
    unit_cost:Decimal=Field(ge=0,decimal_places=2)
    stock_units:int=Field(ge=0)
    daily_demand:float|None=Field(default=None,ge=0)
    forecast_daily_demand:float|None=Field(default=None,ge=0)
    competitor_price:Decimal|None=Field(default=None,gt=0,decimal_places=2)
    promotion_eligible:bool=False
    stockout_risk:bool=False
    source:str=Field(min_length=1)
    fixture:bool=False

class Query(Contract):
    store_id:str
    sku_id:str
    as_of:date
    mode:Literal['recommend','competitive_simulation']='recommend'
    discount_pct:Decimal=Field(default=Decimal(0),ge=0,le=100)
    min_margin:Decimal=Field(default=Decimal('.10'),ge=0,lt=1)
    max_change_pct:Decimal=Field(default=Decimal(10),ge=0,le=50)
    promotion_start:date|None=None
    promotion_end:date|None=None
    @model_validator(mode='after')
    def dates(self):
        if (self.promotion_start is None)!=(self.promotion_end is None):raise ValueError('Both promotion dates required')
        if self.promotion_start and self.promotion_start>self.promotion_end:raise ValueError('Reversed promotion dates')
        return self

class ElasticityEstimator(Protocol):
    def estimate(self,prices:list[float],demand:list[float])->float: ...


def evaluate(rows:list[Price],query:Query)->dict:
    rows=[r for r in rows if r.store_id==query.store_id and r.sku_id==query.sku_id and r.observed_on<=query.as_of]
    if not rows:return {'status':'not_found','recommendation':None}
    if len({r.observed_on for r in rows})!=len(rows):raise ValueError('Duplicate price snapshot')
    r=max(rows,key=lambda r:r.observed_on)
    floor=(r.unit_cost/(1-query.min_margin)).quantize(Decimal('.01'),rounding=ROUND_CEILING)
    target=r.current_price;reasons=[]
    if query.mode=='competitive_simulation':
        if r.competitor_price is None:return {'status':'insufficient_evidence','recommendation':None,'reason':'Competitor observation missing.'}
        target=r.competitor_price-Decimal('.01');reasons.append('Sandbox one-step competitor undercut; not an equilibrium solution.')
    elif query.discount_pct:
        in_window=query.promotion_start is not None and query.promotion_start<=query.as_of<=query.promotion_end
        if r.promotion_eligible and in_window and not r.stockout_risk and r.stock_units>0:
            target=r.current_price*(1-query.discount_pct/100);reasons.append('Eligible dated promotion.')
        else:reasons.append('Promotion blocked by eligibility, dates or stock risk.')
    elif r.stockout_risk and r.daily_demand is not None and r.forecast_daily_demand is not None and r.forecast_daily_demand>r.daily_demand:
        target=r.current_price*Decimal('1.05');reasons.append('Advisory scarcity rule; no elasticity estimate.')
    low=r.current_price*(1-query.max_change_pct/100);high=r.current_price*(1+query.max_change_pct/100)
    low=low.quantize(Decimal('.01'),rounding=ROUND_CEILING)
    high=high.quantize(Decimal('.01'),rounding=ROUND_FLOOR)
    if max(floor,low)>high:
        return {'status':'insufficient_evidence','observed':r.model_dump(mode='json'),'recommendation':None,
                'reason':'Margin floor conflicts with maximum price change; human review required.'}
    target=max(floor,low,min(high,target)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    return {'status':'success','observed':r.model_dump(mode='json'),
            'recommendation':{'price':str(target),'margin_floor':str(floor),'mode':query.mode,'reasons':reasons,
                              'promotion_requested_pct':str(query.discount_pct),'applied_discount_pct':str((r.current_price-target)/r.current_price*100)},
            'operational_write_performed':False,'age_days':(query.as_of-r.observed_on).days,
            'warnings':['Rule-based advisory result; demand elasticity and competitive equilibrium are not fitted.']}
