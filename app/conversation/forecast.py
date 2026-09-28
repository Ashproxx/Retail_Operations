"""Apparel observed-sales forecasting with chronological, shared-fold model selection."""
from dataclasses import dataclass
from datetime import date, timedelta
from math import sqrt
from statistics import mean
from typing import Protocol
from app.conversation.analytics import select_rows
from app.conversation.dates import season


class ForecastProfile(Protocol):
    name: str
    def candidates(self, minimum_training_days: int) -> list[str]: ...


@dataclass(frozen=True)
class ApparelRetailForecastProfile:
    name: str = 'apparel-retail'

    def candidates(self, minimum_training_days):
        models=['naive','moving_average_7','exponential_0.3']
        if minimum_training_days>=14:models.append('seasonal_naive_7')
        if minimum_training_days>=28:models.append('weekday_mean_28')
        if minimum_training_days>=730:models.append('seasonal_naive_365')
        return models


def predict(model, days, values, target):
    if model=='naive': return values[-1]
    if model=='moving_average_7':return mean(values[-7:])
    if model=='exponential_0.3':
        level=values[0]
        for value in values[1:]:level=.3*value+.7*level
        return level
    if model=='weekday_mean_28':
        matching=[v for d,v in zip(days[-28:],values[-28:]) if d.weekday()==target.weekday()]
        return mean(matching)
    lag=365 if model=='seasonal_naive_365' else 7
    index=(target-days[-1]).days
    return values[-lag+(index-1)%lag]


def backtest(days, values, profile=None):
    profile=profile or ApparelRetailForecastProfile()
    start=max(7,len(values)-28)
    if len(values)<14:return []
    results=[]
    for model in profile.candidates(start):
        folds=[]
        for i in range(start,len(values)):
            prediction=predict(model,days[:i],values[:i],days[i])
            folds.append({'training_end':days[i-1].isoformat(),'target':days[i].isoformat(),
                          'prediction':prediction,'actual':values[i]})
        errors=[f['prediction']-f['actual'] for f in folds]
        denom=sum(abs(f['actual']) for f in folds)
        results.append({'model':model,'mae':mean(abs(x) for x in errors),'rmse':sqrt(mean(x*x for x in errors)),
                        'wape':sum(abs(x) for x in errors)/denom if denom else None,
                        'folds':folds,'evaluated_points':len(folds)})
    return sorted(results,key=lambda r:(r['mae'],r['rmse'],r['model']))


def forecast(rows,ctx):
    # Forecast origin is the requested period end, never the latest future observation.
    origin=date.fromisoformat(ctx.period['end'])
    historical=select_rows(rows,ctx,{'start':'0001-01-01','end':origin.isoformat()})
    if not historical:return {'status':'insufficient_data','summary':'No historical sales are available at this forecast origin.'}
    pairs={(r['store_id'],r['sku_id']) for r in historical}
    by_day={}
    for r in historical:
        if r.get('units_sold') is None:continue
        by_day.setdefault(date.fromisoformat(r['date']),{})[(r['store_id'],r['sku_id'])]=float(r['units_sold'])
    if not by_day:return {'status':'insufficient_data','summary':'Units sold are not available for this selection.'}
    days=sorted(by_day)
    if days[-1]!=origin or len(days)<14 or any((b-a).days!=1 for a,b in zip(days,days[1:])):
        return {'status':'insufficient_data','summary':'Need at least 14 contiguous observed days ending at the selected date. Missing days are not zero sales.',
                'available_start':days[0].isoformat(),'available_end':days[-1].isoformat()}
    if any(set(by_day[d])!=pairs for d in days):
        return {'status':'insufficient_data','summary':'Product coverage changes across days. Select a product with complete history; absent products are not assumed to have zero sales.'}
    values=[sum(by_day[d].values()) for d in days]
    evaluated=backtest(days,values)
    winner=evaluated[0];model=winner['model']
    points=[]
    for i in range(1,ctx.horizon+1):
        target=origin+timedelta(days=i);estimate=max(0,predict(model,days,values,target))
        spread=1.96*winner['rmse']*sqrt(i)
        points.append({'date':target.isoformat(),'units':estimate,'lower':max(0,estimate-spread),'upper':estimate+spread})
    stockouts=sum(r.get('closing_stock')==0 or r.get('stockout_risk_flag') is True for r in historical)
    warnings=['Forecast targets observed sales, a demand proxy; it is not a guarantee of unconstrained demand.',
              'Residual bands are heuristic, not calibrated prediction intervals.',
              'Model selection and reported scores share the validation folds; they are not independent holdout accuracy.',
              'Prices/promotions/variants are context, not fitted causal covariates. Missing promotion and supplier data is not invented.']
    if stockouts:warnings.append(f'{stockouts} stock-constrained observations may bias the observed-sales forecast downward.')
    return {'status':'success','summary':f"{ctx.horizon}-day {ctx.product or ctx.category or 'store'} forecast uses {model}; rolling one-step MAE {winner['mae']:.2f} units.",
            'profile':'apparel-retail','forecast':points,'model':model,'validation':evaluated,
            'history':{'start':days[0].isoformat(),'end':days[-1].isoformat(),'days':len(days)},
            'trend':mean(values[-7:])-mean(values[:7]),'calendar':season(origin.isoformat()),
            'weekday_means':{str(w):mean(v for d,v in zip(days,values) if d.weekday()==w) for w in range(7)} if len(days)>=28 else None,
            'monthly_means':{str(m):mean(v for d,v in zip(days,values) if d.month==m) for m in {d.month for d in days}} if len(days)>=365 else None,
            'warnings':warnings,'fixture':any(r.get('fixture') for r in historical),
            'sources':sorted({r['source'] for r in historical})}
