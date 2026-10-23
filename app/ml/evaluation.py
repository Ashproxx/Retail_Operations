"""Time-ordered validation, explicit embargo and paired error comparison."""
from datetime import date, timedelta
from math import sqrt, ceil
from statistics import mean
import random
from app.conversation.forecast import ApparelRetailForecastProfile
from app.ml.models import Baseline
from app.ml.features import validate_series


def metrics(actual: list[float], predicted: list[float], training: list[float]) -> dict:
    if not actual or len(actual)!=len(predicted):
        raise ValueError('Need aligned nonempty scores')
    errors = [p-a for a,p in zip(actual,predicted)]
    scale = mean(abs(a-b) for a,b in zip(training[7:],training[:-7])) if len(training)>7 else None
    mae = mean(abs(e) for e in errors)
    return {'mae':mae, 'rmse':sqrt(mean(e*e for e in errors)), 'bias':mean(errors),
            'wape':sum(abs(e) for e in errors)/sum(actual) if sum(actual) else None,
            'mase':mae/scale if scale else None, 'n':len(actual)}


def legacy_parity(days: list[date], values: list[float]) -> list[dict]:
    validate_series(days,values,contiguous=True)
    if len(values)<14:
        return []
    start=max(7,len(values)-28)
    results=[]
    for name in ApparelRetailForecastProfile().candidates(start):
        folds=[]
        for i in range(start,len(values)):
            prediction=Baseline(name).fit(days[:i],values[:i]).predict([days[i]])[0]
            folds.append({'training_end':days[i-1].isoformat(),'target':days[i].isoformat(),
                          'prediction':prediction,'actual':values[i]})
        score=metrics(values[start:],[r['prediction'] for r in folds],values[:start])
        results.append({'model':name,**{k:score[k] for k in ('mae','rmse','wape')},'folds':folds,'evaluated_points':len(folds)})
    return sorted(results,key=lambda r:(r['mae'],r['rmse'],r['model']))


def rolling_origin(days: list[date], values: list[float], factory, origins: list[date], horizon: int,
                   *, minimum: int = 56, test_start: date) -> dict:
    validate_series(days,values)
    if horizon not in (1,7,14,28) or len(origins)<4 or origins!=sorted(set(origins)):
        raise ValueError('Require four ordered origins and an approved horizon')
    lookup=dict(zip(days,values)); folds=[]; exclusions=[]
    for origin in origins:
        targets=[origin+timedelta(days=horizon+i) for i in range(1,horizon+1)]
        if targets[-1]>=test_start:
            raise ValueError('Validation must not read the final test block')
        train_days=[d for d in days if d<=origin]; train=[lookup[d] for d in train_days]
        if len(train)<minimum or not train_days or train_days[-1]!=origin or any(t not in lookup for t in targets):
            exclusions.append({'origin':origin.isoformat(),'reason':'insufficient observed coverage'}); continue
        try:
            validate_series(train_days,train,contiguous=True)
        except ValueError:
            exclusions.append({'origin':origin.isoformat(),'reason':'missing training dates'}); continue
        model=factory().fit(train_days,train)
        predictions=model.predict(targets); actual=[lookup[t] for t in targets]
        folds.append({'origin':origin.isoformat(),'gap_days':horizon,'first_lead':horizon+1,
                      'targets':[t.isoformat() for t in targets],'actual':actual,'predictions':predictions,
                      'metrics':metrics(actual,predictions,train)})
    return {'folds':folds,'exclusions':exclusions,'status':'VERIFIED' if len(folds)>=4 else 'INSUFFICIENT_COVERAGE'}


def paired_bootstrap(candidate_errors: list[float], baseline_errors: list[float], *, seed: int=42,
                     trials: int=2000, block: int=7) -> dict:
    if len(candidate_errors)!=len(baseline_errors) or not candidate_errors or trials<100 or block<1:
        raise ValueError('Invalid paired bootstrap input')
    differences=[abs(a)-abs(b) for a,b in zip(candidate_errors,baseline_errors)]
    if len(differences)<2*block:
        return {'status':'INCONCLUSIVE','reason':'fewer than two temporal blocks'}
    rng=random.Random(seed); means=[]; n=len(differences)
    for _ in range(trials):
        samples=[]
        for _ in range(ceil(n/block)):
            start=rng.randrange(n-block+1); samples.extend(differences[start:start+block])
        means.append(mean(samples[:n]))
    means.sort(); lower=means[int(.025*trials)]; upper=means[min(trials-1,int(.975*trials))]
    return {'status':'VERIFIED','mean_difference':mean(differences),'lower':lower,'upper':upper,'candidate_better':upper<0}
