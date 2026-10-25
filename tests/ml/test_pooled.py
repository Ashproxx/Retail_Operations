from datetime import date, timedelta
import pytest
from app.ml.pooled import PooledBoosting
from scripts.evaluate_pooled_forecasting import evaluate


def series():
    days=[date(2026,2,4)+timedelta(days=i) for i in range(56)]
    return {('A',):(days,[10+i%7 for i in range(56)]),
            ('B',):(days,[20+i%7 for i in range(56)])}


def test_recursive_predictions_repeat_without_mutating_history():
    model=PooledBoosting().fit(series()); before={k:dict(v) for k,v in model.history.items()}
    targets=[date(2026,4,15),date(2026,4,28)]
    predicted=model.predict(('A',),targets)
    assert predicted == model.predict(('A',),targets)
    assert all(v >= 0 for v in predicted)
    assert model.history == before
    with pytest.raises(ValueError):model.predict(('unseen',),targets)
    with pytest.raises(ValueError):model.predict(('A',),[date(2026,3,31)])


def test_reject_gaps_origins_and_future_evidence():
    data=series(); days,values=data[('B',)]
    data[('B',)]=(days[:-1],values[:-1])
    with pytest.raises(ValueError):PooledBoosting().fit(data)
    data=series();data[('B',)]=([d+timedelta(days=1) for d in days],values)
    with pytest.raises(ValueError,match='Common origin'):PooledBoosting().fit(data)
    with pytest.raises(ValueError,match='final-test'):
        evaluate([(('A',),date(2026,8,5),1)])
    report=evaluate([(('A',),date(2026,3,31),1)])
    assert report['status']=='UNVERIFIED' and len(report['excluded'])==1
