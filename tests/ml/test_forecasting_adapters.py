from datetime import date,timedelta
import math
import pytest
from app.ml.forecasting import ForecastModel,features
from scripts.benchmark_forecasting import training,select_candidate


@pytest.mark.parametrize('name',['ets','sarima','sarimax_calendar','ridge','lasso','hist_gradient','random_forest','extra_trees','hist_quantile'])
def test_adapters_future_only_and_repeatable(name):
    pytest.importorskip('statsmodels' if name in ('ets','sarima','sarimax_calendar') else 'sklearn')
    days=[date(2025,1,1)+timedelta(days=i) for i in range(100)]
    values=[10+(i%7)*2+(i%3) for i in range(100)]
    model=ForecastModel(name,quantile=.5 if name=='hist_quantile' else None).fit(days,values)
    targets=[days[-1]+timedelta(days=i) for i in (1,7,14,28)]
    predicted=model.predict(targets)
    assert len(predicted)==4 and all(math.isfinite(x) and x>=0 for x in predicted)
    assert model.predict(targets)==pytest.approx(predicted)
    with pytest.raises(ValueError):model.predict([days[-1]])
    assert model.history==dict(zip(days,values))


def test_past_features_and_contiguous_tail():
    days=[date(2025,1,1)+timedelta(days=i) for i in range(100)]
    history=dict(zip(days,range(100)))
    feature=features(history,days[50])
    assert features({**history,days[51]:9999},days[50])==feature
    assert training(days[1:],list(range(1,100)),days[-1])[0][0]==days[1]
    with pytest.raises(ValueError):training(days[::2],list(range(50)),days[-1])


def test_selection_does_not_use_calibration_fold():
    def row(name,prediction,last):
        return {'model':name,'folds':[{'actual':[10]*56,'predicted':[prediction]*56} for _ in range(3)]+[{'actual':[10]*56,'predicted':[last]*56}]}
    a=select_candidate([row('naive',11,1000),row('ridge',12,10)],7)
    b=select_candidate([row('naive',11,10),row('ridge',12,1000)],7)
    assert a==b and a['candidate']=='naive'
