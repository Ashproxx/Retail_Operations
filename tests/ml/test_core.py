from datetime import date, datetime, timedelta, timezone
import json
import pytest
from app.conversation.forecast import backtest
from app.ml.models import Baseline
from app.ml.features import at_origin
from app.ml.evaluation import legacy_parity, rolling_origin, paired_bootstrap, metrics
from app.ml.registry import save, load
from app.ml.monitor import freshness, drift
from app.ml.explain import permutation_importance


def series(n=200):
    return [date(2025,1,1)+timedelta(days=i) for i in range(n)], [10+i%7 for i in range(n)]


def test_parity_and_artifact(tmp_path):
    days,values=series()
    assert legacy_parity(days,values)==backtest(days,values)
    for name in ['naive','moving_average_7','exponential_0.3','seasonal_naive_7','weekday_mean_28']:
        model=Baseline(name).fit(days,values);path=tmp_path/(name+'.json')
        save(path,model,source_hash='a'*64,features=['units'],metrics={},commit='test')
        target=[days[-1]+timedelta(days=7)]
        assert load(path).predict(target)==model.predict(target)
        artifact=json.loads(path.read_text());artifact['payload']['values'][0]=999
        path.write_text(json.dumps(artifact))
        with pytest.raises(ValueError):load(path)
    with pytest.raises(ValueError):Baseline('not_a_model')
    with pytest.raises(ValueError):Baseline('seasonal_naive_365').fit(days,values)


def test_feature_leakage_and_missing_calendar_day():
    days,values=series();cutoff=days[80];target=cutoff+timedelta(days=1)
    before=at_origin(days,values,cutoff,target)
    altered=values[:81]+[99999]*119
    assert at_origin(days,altered,cutoff,target)==before
    assert at_origin(days,values,cutoff,cutoff+timedelta(days=7))['lag_1'] is None
    days.pop(80);values.pop(80)
    features=at_origin(days,values,cutoff,target)
    assert features['lag_1'] is None and features['mean_7'] is None and features['count_7']==6


def test_validation_gap_and_final_test_exclusion():
    days,values=series(366);origins=[days[i] for i in [70,100,130,160]]
    factory=lambda:Baseline('naive')
    result=rolling_origin(days,values,factory,origins,7,test_start=days[300])
    assert result['status']=='VERIFIED'
    assert result['folds'][0]['targets'][0]==(origins[0]+timedelta(days=8)).isoformat()
    assert rolling_origin(days,values[:301]+[9999]*65,factory,origins,7,test_start=days[300])==result
    with pytest.raises(ValueError):rolling_origin(days,values,factory,origins,28,test_start=days[200])
    missing=rolling_origin(days[1:],values[1:],factory,origins,7,test_start=days[300])
    assert len(missing['folds'])==4
    days.pop(20);values.pop(20)
    assert rolling_origin(days,values,factory,origins,7,test_start=days[299])['status']=='INSUFFICIENT_COVERAGE'


def test_statistics_and_explanation():
    assert metrics([0],[0],[1]*30)['wape'] is None
    assert metrics([1],[2],[1]*30)['mase'] is None
    assert paired_bootstrap([1]*28,[4]*28)['candidate_better']
    assert paired_bootstrap([1],[4])['status']=='INCONCLUSIVE'
    rows=[{'signal':i,'noise':0} for i in range(20)]
    result=permutation_importance(lambda rows:[r['signal'] for r in rows],rows,list(range(20)))
    assert result['increase_in_mae']['signal']>0 and result['increase_in_mae']['noise']==0
    assert rows[0]=={'signal':0,'noise':0}
    now=datetime.now(timezone.utc)
    assert freshness(now-timedelta(hours=2),now)['status']=='amber'
    assert freshness(now-timedelta(hours=6),now)['status']=='red'
    assert freshness(now+timedelta(hours=1),now)['status']=='invalid_future_timestamp'
    assert drift([1]*28,[10]*7)['retraining_review']


def test_scoped_sql_features(tmp_path,monkeypatch):
    from app.enterprise import imports
    from app.services.database_service import Database
    from app.api.schemas import RequestContext
    from app.ml.features import daily_series
    from app.security.policy import AccessDenied
    from tests.phase3.test_imports import small_sales
    db=Database('sqlite:///'+str(tmp_path/'db'));source=tmp_path/'sales.xlsx';source.write_bytes(b'fixture')
    monkeypatch.setattr(imports,'sheets',lambda *args:small_sales());imports.import_sales(db,source)
    outside=RequestContext(session_id='test',principal_id='manager',role='STORE_MANAGER',store_ids=['outside'])
    assert daily_series(db,outside,date(2030,1,1))=={}
    hr=RequestContext(session_id='test',principal_id='hr',role='HR_ADMIN')
    with pytest.raises(AccessDenied):daily_series(db,hr,date(2030,1,1))
    db.close()
