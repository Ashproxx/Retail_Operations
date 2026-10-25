from datetime import date,timedelta
import pytest
from app.ml.intervals import conformal_radius,intervals,interval_metrics,pinball
from app.ml.intermittent import Intermittent


def test_conformal_finite_sample_rank_and_small_sample():
    assert conformal_radius(list(range(1,20)),.95)==19
    with pytest.raises(ValueError):conformal_radius([1,2,3],.95)
    with pytest.raises(ValueError):conformal_radius([float('nan')],.5)
    bands=intervals([2,20],list(range(1,20)),.8)
    assert bands[0]['lower']==0
    assert interval_metrics([2,100],bands)['coverage']==.5
    assert pinball([10],[8],.9)==pytest.approx(1.8)
    assert pinball([10],[12],.9)==pytest.approx(.2)


def test_intermittent_counts_gaps_and_posterior():
    days=[date(2026,1,1)+timedelta(days=i) for i in range(20)]
    target=[days[-1]+timedelta(days=1)]
    for name in ['croston','sba','tsb','gamma_poisson']:
        model=Intermittent(name).fit(days,[2]*20)
        expected=2 if name in ('croston','tsb') else 1.9 if name=='sba' else 41/21
        assert model.predict(target)==pytest.approx([expected])
        with pytest.raises(ValueError):model.fit(days[::2],[2]*10)
        with pytest.raises(ValueError):model.fit(days,[.5]*20)
    assert Intermittent('croston').fit(days,[0]*20).predict(target)==[0]
    assert Intermittent('tsb').fit(days,[10]+[0]*19).predict(target)[0]<2
    with pytest.raises(ValueError):Intermittent(alpha=0)
