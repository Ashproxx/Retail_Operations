from datetime import date,timedelta
import pytest
from app.ml.forecasting import ForecastModel,FEATURES
from app.ml.supplement import frozen_rows,evaluate


def test_frozen_feature_rows_match_recursive_predictions():
    days=[date(2026,1,1)+timedelta(days=i) for i in range(70)]
    values=[30+i%7*5 for i in range(70)]
    model=ForecastModel('hist_gradient').fit(days,values)
    original=dict(model.history)
    targets=[days[-1]+timedelta(days=i) for i in [15,16,28]]
    rows=frozen_rows(model,targets)
    actual=[max(0,float(v)) for v in model.model.predict([[r[f] for f in FEATURES] for r in rows])]
    assert actual==pytest.approx(model.predict(targets))
    assert model.history==original


def test_supplement_rejects_later_and_missing_dates():
    days=[date(2025,11,1)+timedelta(days=i) for i in range(300)]
    with pytest.raises(ValueError,match='final-test'):evaluate(days,[1]*300)
    with pytest.raises(ValueError):evaluate(days[::2],[1]*150)
