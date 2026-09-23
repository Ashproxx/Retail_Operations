import pytest
from pydantic import ValidationError
from app.agents.analytics.domain import Sale,Query,evaluate,agent_metrics

def r(**kw):return Sale(**dict(dict(store_id='s',sku_id='a',category='shirts',day='2026-01-01',units_sold=3,unit_price_inr='0.10',closing_stock=2,reorder_point=5,source='fixture://sales',fixture=True),**kw))
def q(**kw):return Query(**dict(dict(start='2026-01-01',end='2026-01-02'),**kw))

def test_exact_revenue_and_latest_stock_counts():
    result=evaluate([r(),r(day='2026-01-02',closing_stock=10)],q())
    assert result['summary']['sales_inr']=='0.60'
    assert result['summary']['low_stock_count']==0
    assert result['summary']['units_sold']==6
    assert result['summary']['inventory_turnover_proxy']==1

def test_grouping_and_rank_ties():
    result=evaluate([r(),r(store_id='b',sku_id='b',category='pants',units_sold=0,closing_stock=0,stockout_risk_flag=True)],q())
    assert result['top_skus'][0]==('a',3)
    assert result['slow_moving_skus'][0]==('b',0)
    assert result['summary']['stockout_risk_count']==1
    assert result['summary']['unknown_risk_count']==1
    assert result['sales_by_category']=={'pants':'0.00','shirts':'0.30'}

def test_filters_empty_duplicate_zero_stock():
    assert evaluate([r()],q(store_id='missing'))['status']=='not_found'
    assert evaluate([r()],q(sku_id='missing'))['status']=='not_found'
    assert evaluate([r(closing_stock=0)],q())['summary']['inventory_turnover_proxy'] is None
    with pytest.raises(ValueError):evaluate([r(),r()],q())

@pytest.mark.parametrize('kw',[{'unit_price_inr':'NaN'},{'units_sold':-1},{'closing_stock':-1}])
def test_invalid_rows(kw):
    with pytest.raises(ValidationError):r(**kw)

def test_dates_and_metrics():
    with pytest.raises(ValidationError):q(start='2026-02-01')
    from app.api.schemas import AuditEvent,Role
    from uuid import uuid4
    events=[AuditEvent(request_id=uuid4(),session_id='fixture',user_role=Role.ANALYST,confidence=0,latency_ms=10,final_status='error',agents_called=['inventory','inventory'])]
    assert agent_metrics(events)['inventory']['requests']==1
    assert agent_metrics(events)['inventory']['error_requests']==1
    assert agent_metrics([])=={}

def test_agent_empty():
    import asyncio
    from app.agents.analytics.agent import Agent
    from app.api.schemas import QueryRequest,RequestContext,Role
    result=asyncio.run(Agent().run(QueryRequest(message=q().model_dump_json(),session_id='t'),RequestContext(session_id='t',principal_id='u',role=Role.ANALYST,store_ids=['s'])))
    assert result.status=='not_found'
