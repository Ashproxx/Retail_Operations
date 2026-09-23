import pytest
from pydantic import ValidationError
from app.agents.supply.domain import Vendor,Query,evaluate

def r(**kw):return Vendor(**dict(dict(store_id='s',vendor_id='v',sku_id='a',observed_on='2026-01-01',promised_lead_days=2,observed_lead_days=[1,3],capacity=20,unit_cost='10',source='fixture://vendor',fixture=True),**kw))
def q(**kw):return Query(**dict(dict(store_id='s',sku_id='a',as_of='2026-01-02',daily_demand=5,stock_units=5,coverage_days=4),**kw))

def test_comparison_and_disruption():
    result=evaluate([r(),r(vendor_id='cheap',capacity=2,unit_cost='1')],q(disruption_multiplier=2))
    assert result['required_quantity']==15 and result['recommended_vendor']=='v'
    assert result['vendors'][0]['scenario_lead_days']==4
    assert result['vendors'][0]['historical_late_fraction']==.5
    assert result['vendors'][0]['lead_time_stockout_risk']

def test_shortfall_no_recommendation_and_unknown_history():
    result=evaluate([r(capacity=1,observed_lead_days=[])],q())
    assert result['recommended_vendor'] is None
    assert result['vendors'][0]['historical_late_fraction'] is None

def test_sop_evidence_or_absence():
    assert evaluate([r()],q(mode='sop'))['status']=='insufficient_evidence'
    result=evaluate([r(sop_excerpt='Fixture receiving checklist',sop_source='fixture://sop')],q(mode='sop'))
    assert result['sources'][0]['fixture']

def test_negotiation_history():
    row=r(negotiations=[{'offered':'12','settled':'10','accepted':True}])
    assert evaluate([row],q())['vendors'][0]['bargaining_history']['mean_settled_price']=='10'

@pytest.mark.parametrize('kw',[{'capacity':-1},{'observed_lead_days':[-1]},{'observed_lead_days':[float('nan')]},{'sop_excerpt':'unattributed'}])
def test_invalid(kw):
    with pytest.raises(ValidationError):r(**kw)

def test_missing_future_duplicate():
    assert evaluate([],q())['status']=='not_found'
    assert evaluate([r()],q(vendor_id='unknown'))['status']=='not_found'
    assert evaluate([r(observed_on='2026-03-01')],q())['status']=='not_found'
    with pytest.raises(ValueError):evaluate([r(),r()],q())
