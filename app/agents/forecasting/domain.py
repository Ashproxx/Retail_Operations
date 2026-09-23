from datetime import date,timedelta
from math import sqrt
from statistics import mean,pstdev
from typing import Literal,Protocol
from pydantic import Field
from app.api.schemas import Contract

class Sale(Contract):
    store_id:str=Field(min_length=1)
    sku_id:str=Field(min_length=1)
    day:date
    units:float=Field(ge=0)
    source:str=Field(min_length=1)
    fixture:bool=False

class Query(Contract):
    store_id:str
    sku_id:str
    as_of:date
    horizon:int=Field(default=7,ge=1,le=90)
    method:Literal['moving_average','exponential']='moving_average'
    window:int=Field(default=7,ge=2,le=90)
    alpha:float=Field(default=.3,gt=0,le=1)

class BayesianEstimator(Protocol):
    def posterior(self, observations:list[float])->dict: ...


def baseline(values:list[float],query:Query)->float:
    if query.method=='moving_average':return mean(values[-query.window:])
    level=values[0]
    for value in values[1:]:level=query.alpha*value+(1-query.alpha)*level
    return level


def evaluate(rows:list[Sale],query:Query)->dict:
    rows=sorted([r for r in rows if r.store_id==query.store_id and r.sku_id==query.sku_id and r.day<=query.as_of],key=lambda r:r.day)
    if not rows:return {'status':'not_found','forecast':[]}
    if len({r.day for r in rows})!=len(rows):raise ValueError('Duplicate daily observation')
    gaps=[(b.day-a.day).days for a,b in zip(rows,rows[1:])]
    if len(rows)<query.window or any(g!=1 for g in gaps):
        return {'status':'insufficient_evidence','forecast':[], 'reason':'Need contiguous daily observations covering the window; gaps are not zero sales.'}
    values=[r.units for r in rows]
    if rows[-1].day!=query.as_of:return {'status':'insufficient_evidence','forecast':[],'reason':'History does not reach as_of.'}
    level=baseline(values,query)
    errors=[values[i]-baseline(values[:i],query) for i in range(query.window,len(values))]
    rmse=sqrt(mean([x*x for x in errors])) if errors else None
    mae=mean([abs(x) for x in errors]) if errors else None
    forecasts=[{'day':(query.as_of+timedelta(days=i)).isoformat(),'units':level,
                'lower':None if rmse is None else max(0,level-1.96*rmse*sqrt(i)),
                'upper':None if rmse is None else level+1.96*rmse*sqrt(i)} for i in range(1,query.horizon+1)]
    weekdays={str(d):mean([r.units for r in rows if r.day.weekday()==d]) for d in range(7)} if len(rows)>=28 else None
    first=mean(values[:query.window]);last=mean(values[-query.window:])
    return {'status':'success','forecast':forecasts,'model':query.method+'-v1','historical_days':len(rows),
            'history_start':rows[0].day.isoformat(),'history_end':rows[-1].day.isoformat(),
            'mean_trend_change':last-first,'weekday_means':weekdays,
            'evaluation':{'rolling_one_step_mae':mae,'rolling_one_step_rmse':rmse,'evaluated_points':len(errors)},
            'sources':sorted({r.source for r in rows}),'fixture':any(r.fixture for r in rows),
            'warnings':['Intervals are heuristic residual bands, not calibrated prediction intervals.',
                        'No promotion covariates or Bayesian posterior fitted.']+(['No holdout residuals; uncertainty unavailable.'] if not errors else [])}
