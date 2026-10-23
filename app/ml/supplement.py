"""Pre-test exploratory quantile and importance evidence; never promotes a model."""
from datetime import date, timedelta
from app.ml.features import validate_series
from app.ml.forecasting import ForecastModel, FEATURES, features
from app.ml.models import Baseline
from app.ml.intervals import intervals, interval_metrics, pinball
from app.ml.explain import permutation_importance
from app.ml.evaluation import metrics


def frozen_rows(model, targets):
    future=[model.days[-1]+timedelta(days=i) for i in range(1,(max(targets)-model.days[-1]).days+1)]
    history=dict(model.history)
    history.update(zip(future,model.predict(future)))
    return [dict(zip(FEATURES,features(history,d))) for d in targets]


def evaluate(days,values):
    validate_series(days,values,contiguous=True)
    origin=date(2026,3,31);end=date(2026,4,28)
    if days[-1]!=end or days[0]>date(2025,12,1):
        raise ValueError('Fixed supplemental window required; no final-test dates permitted')
    lookup=dict(zip(days,values))
    train_days=[d for d in days if d<=origin];train=[lookup[d] for d in train_days]
    targets=[origin+timedelta(days=i) for i in range(15,29)]
    actual=[lookup[d] for d in targets]
    quantiles={q:ForecastModel('hist_quantile',quantile=q).fit(train_days,train).predict(targets) for q in [.1,.5,.9]}
    crossings=sum(not lo<=mid<=hi for lo,mid,hi in zip(quantiles[.1],quantiles[.5],quantiles[.9]))
    ordered=list(zip(*(sorted(row) for row in zip(quantiles[.1],quantiles[.5],quantiles[.9]))))
    bands=[{'lower':lo,'upper':hi} for lo,hi in zip(ordered[0],ordered[2])]
    point=Baseline('weekday_mean_28').fit(train_days,train).predict(targets)
    calibration_origin=date(2026,2,28)
    calibration_days=[d for d in days if d<=calibration_origin]
    calibration_values=[lookup[d] for d in calibration_days]
    residual_dates=[calibration_origin+timedelta(days=i) for i in range(1,32)]
    residual_predictions=Baseline('weekday_mean_28').fit(calibration_days,calibration_values).predict(residual_dates)
    residuals=[lookup[d]-p for d,p in zip(residual_dates,residual_predictions)]
    baseline_bands=intervals(point,residuals,.8)
    model=ForecastModel('hist_gradient').fit(train_days,train)
    rows=frozen_rows(model,targets)
    def predict(data):
        return [max(0,float(p)) for p in model.model.predict([[r[f] for f in FEATURES] for r in data])]
    importance=permutation_importance(predict,rows,actual,seed=42,repeats=5)
    return {'status':'EXPLORATORY_PRETEST_VALIDATION','origin':origin.isoformat(),
        'targets':[d.isoformat() for d in targets],'observations':len(actual),'horizon':14,'embargo_days':14,
        'quantile_raw_pinball':{str(q):pinball(actual,quantiles[q],q) for q in quantiles},
        'quantile_ordered_pinball':{str(q):pinball(actual,list(ordered[i]),q) for i,q in enumerate(quantiles)},
        'quantile_crossing_dates':crossings,'quantile_ordered_80':interval_metrics(actual,bands),
        'baseline_conformal_80':interval_metrics(actual,baseline_bands),
        'baseline_point_metrics':metrics(actual,point,train),
        'quantile_median_metrics':metrics(actual,list(ordered[1]),train),
        'importance':importance, 'limitations':[
            'One chain origin and fourteen validation observations; not independent final-test accuracy.',
            'Each quantile adapter recursively feeds its own predictions; multi-step quantile calibration is not guaranteed.',
            'Per-date sorting repairs quantile crossing before scoring; both raw and repaired losses are reported.',
            'Baseline conformal residuals come from a February fit predicting March; pooled leads and distribution shift limit coverage.',
            'Importance permutes fixed recursive feature rows, not complete forecast trajectories; correlated features may mask each other.',
            'No retraining on validation labels, hyperparameter search, model promotion or change to frozen test evidence.']}
