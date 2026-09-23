from datetime import date,timedelta
import asyncio
import pytest
from pydantic import ValidationError
from app.agents.forecasting.domain import Sale,Query,evaluate

def rows(n=28):return [Sale(store_id='s',sku_id='a',day=date(2026,1,1)+timedelta(days=i),units=10,source='fixture://sales',fixture=True) for i in range(n)]
def q(**kw):return Query(**dict(dict(store_id='s',sku_id='a',as_of='2026-01-28'),**kw))
@pytest.mark.parametrize('method',['moving_average','exponential'])
def test_constant_series(method):
    result=evaluate(rows(),q(method=method))
    assert [p['units'] for p in result['forecast']]==[10]*7
    assert result['evaluation']['rolling_one_step_mae']==0
    assert result['weekday_means']=={str(i):10 for i in range(7)}
    assert result['forecast'][0]['day']=='2026-01-29'

def test_trend_and_no_future_leakage():
    r=rows();r[-1]=r[-1].model_copy(update={'units':24})
    assert evaluate(r,q())['mean_trend_change']==2
    future=Sale(store_id='s',sku_id='a',day='2026-01-29',units=1000,source='fixture://sales')
    assert evaluate(r+[future],q())==evaluate(r,q())

def test_missing_sparse_stale():
    assert evaluate([],q())['status']=='not_found'
    assert evaluate(rows(3),q())['status']=='insufficient_evidence'
    r=rows();del r[4]
    assert evaluate(r,q())['status']=='insufficient_evidence'
    assert evaluate(rows(27),q())['status']=='insufficient_evidence'

def test_invalid_duplicate_and_uncertainty():
    with pytest.raises(ValueError):evaluate(rows()+[rows()[0]],q())
    with pytest.raises(ValidationError):q(horizon=0)
    with pytest.raises(ValidationError):q(alpha=1.1)
    r=evaluate(rows(7),q(as_of='2026-01-07'))
    assert r['forecast'][0]['upper'] is None
    assert r['evaluation']['evaluated_points']==0

def test_store_sku_scope():
    assert evaluate(rows(),q(sku_id='x'))['status']=='not_found'
    from app.agents.forecasting.agent import Agent
    from app.api.schemas import QueryRequest,RequestContext,Role
    context=RequestContext(session_id='t',principal_id='u',role=Role.ANALYST,store_ids=['other'])
    result=asyncio.run(Agent(rows()).run(QueryRequest(session_id='t',message=q().model_dump_json()),context))
    assert result.status=='escalated'
