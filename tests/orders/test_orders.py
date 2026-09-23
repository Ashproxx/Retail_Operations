import pytest
from pydantic import ValidationError
from app.agents.orders.domain import Order,Query,evaluate,validate_transition

def r(**kw):return Order(**dict(dict(store_id='s',order_id='o',sku_id='shirt',quantity=5,state='created',placed_at='2026-01-01T00:00:00Z',updated_at='2026-01-01T00:00:00Z',promised_at='2026-01-03T00:00:00Z',source='fixture://order',fixture=True),**kw))
def q(**kw):return Query(**dict(dict(store_id='s',order_id='o',as_of='2026-01-02T00:00:00Z'),**kw))

def test_pending_overdue_cancelled():
    assert evaluate([r()],q())['sla']=='pending'
    assert evaluate([r()],q(as_of='2026-01-04T00:00:00Z'))['overdue_hours']==24
    assert evaluate([r(state='cancelled')],q(as_of='2026-01-04T00:00:00Z'))['sla']=='not_applicable'

def test_delivered_and_eta_risk():
    order=r(state='delivered',updated_at='2026-01-02T00:00:00Z',delivered_at='2026-01-02T00:00:00Z')
    assert evaluate([order],q())['sla']=='on_time'
    assert evaluate([r(estimated_arrival='2026-01-04T00:00:00Z')],q())['delay_risk']

def test_allocation_and_shortfall():
    sources=[dict(source_id='a',capacity=2,unit_fulfillment_cost='1',arrival_at='2026-01-03T00:00:00Z'),dict(source_id='b',capacity=4,unit_fulfillment_cost='2',arrival_at='2026-01-03T00:00:00Z')]
    result=evaluate([r(fulfillment_sources=sources)],q(mode='allocation'))
    assert result['split_shipment'] and result['total_variable_cost']=='8'
    assert sum(a['quantity'] for a in result['allocations'])==5
    result=evaluate([r(fulfillment_sources=sources[:1])],q(mode='allocation'))
    assert result['status']=='insufficient_evidence' and result['unallocated_quantity']==3

def test_late_sources_excluded():
    sources=[dict(source_id='a',capacity=20,unit_fulfillment_cost='1',arrival_at='2026-01-04T00:00:00Z')]
    assert evaluate([r(fulfillment_sources=sources)],q(mode='allocation'))['allocations']==[]

@pytest.mark.parametrize('kw',[{'state':'delivered'},{'state':'shipped'},{'quantity':0},{'placed_at':'2026-01-01T00:00:00'},{'updated_at':'2025-01-01T00:00:00Z'}])
def test_invalid_order(kw):
    with pytest.raises(ValidationError):r(**kw)

def test_missing_and_transitions():
    assert evaluate([],q())['status']=='not_found'
    assert evaluate([r()],q(order_id='unknown'))['order'] is None
    with pytest.raises(ValueError):evaluate([r(),r()],q())
    validate_transition('created','packed')
    with pytest.raises(ValueError):validate_transition('delivered','shipped')
