from datetime import date
import pytest
from pydantic import ValidationError
from app.agents.inventory.domain import Snapshot,Query,evaluate

def row(**kw):
    return Snapshot(**dict(dict(store_id='Bandra',sku_id='shirt',observed_on='2026-09-01',closing_stock=5,
      reorder_point=10,lead_days=3,daily_demand=4,demand_std=2,opening_stock=9,source='fixture://inventory',fixture=True),**kw))
def query(**kw):return Query(as_of=date(2026,9,2),**kw)

def test_known_reorder_calculation():
    result=evaluate([row()],query(service_z=0,review_days=2))['items'][0]
    assert result['recommended_quantity']==15
    assert result['computed_reorder_point']==12
    assert result['stockout_risk'] is True
    assert result['stock_movement']==-4
    assert result['fixture'] is True

def test_safety_stock_and_position():
    result=evaluate([row(on_order=20,reserved=2)],query(service_z=2))['items'][0]
    assert result['safety_stock']==pytest.approx(4*3**.5)
    assert result['inventory_position']==23
    assert result['available_stock']==3

@pytest.mark.parametrize('kw',[{'closing_stock':-1},{'reserved':6},{'lead_days':-1},{'daily_demand':float('nan')}])
def test_bad_input(kw):
    with pytest.raises(ValidationError):row(**kw)

def test_latest_cutoff_and_filter():
    rows=[row(),row(observed_on='2026-09-02',closing_stock=30),row(observed_on='2026-09-03',closing_stock=0)]
    assert evaluate(rows,query())['items'][0]['available_stock']==30
    assert evaluate(rows,query(action='low_stock'))['items']==[]
    assert evaluate(rows,query(store_id='missing'))['status']=='not_found'
    assert evaluate(rows,query(sku_id='missing'))['items']==[]

def test_duplicate():
    with pytest.raises(ValueError):evaluate([row(),row()],query())

def test_missing_demand_and_zero():
    item=evaluate([row(daily_demand=None,demand_std=None)],query())['items'][0]
    assert item['recommended_quantity'] is None and item['stockout_risk'] is None
    assert item['warnings']
    assert evaluate([row(daily_demand=0)],query())['items'][0]['days_of_cover'] is None

def test_stockout_overstock_comparison():
    rows=[row(closing_stock=0),row(store_id='Andheri',closing_stock=200)]
    assert len(evaluate(rows,query(action='overstock'))['items'])==1
    assert len(evaluate(rows,query(action='stockout_risk'))['items'])==1
    assert evaluate(rows,query())['store_available_totals']=={'Bandra':0,'Andheri':200}

def test_agent_scope_and_missing_data():
    import asyncio
    from app.agents.inventory.agent import Agent
    from app.api.schemas import QueryRequest,RequestContext,Role
    context=RequestContext(session_id='t',principal_id='test',role=Role.INVENTORY_MANAGER,store_ids=['Bandra'])
    async def run():
        agent=Agent([row(),row(store_id='Andheri')])
        result=await agent.run(QueryRequest(session_id='t',message='{"as_of":"2026-09-02"}'),context)
        assert len(result.data['items'])==1 and result.data['fixture']
        assert result.data['audit']['agents_called']==['inventory']
        result=await agent.run(QueryRequest(session_id='t',message='{"as_of":"2026-09-02","store_id":"Andheri"}'),context)
        assert result.status=='escalated'
        assert (await Agent().run(QueryRequest(session_id='t',message='{"as_of":"2026-09-02"}'),context)).status=='not_found'
    asyncio.run(run())
