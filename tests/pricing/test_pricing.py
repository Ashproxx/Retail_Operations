import pytest
from pydantic import ValidationError
from app.agents.pricing.domain import Price,Query,evaluate

def row(**kw):return Price(**dict(dict(store_id='s',sku_id='a',observed_on='2026-01-01',current_price='100',unit_cost='50',stock_units=20,promotion_eligible=True,source='fixture://prices',fixture=True),**kw))
def q(**kw):return Query(**dict(dict(store_id='s',sku_id='a',as_of='2026-01-02'),**kw))

def test_promotion_and_margin_floor():
    result=evaluate([row()],q(discount_pct=20,promotion_start='2026-01-01',promotion_end='2026-01-03',max_change_pct=30))
    assert result['recommendation']['price']=='80.00'
    assert result['observed']['current_price']=='100'
    assert not result['operational_write_performed']
    result=evaluate([row(unit_cost='85')],q(discount_pct=50,promotion_start='2026-01-01',promotion_end='2026-01-03',max_change_pct=50))
    assert result['recommendation']['price']=='94.45'

@pytest.mark.parametrize('kw',[{'stockout_risk':True},{'promotion_eligible':False},{'stock_units':0}])
def test_blocked_promotion(kw):
    assert evaluate([row(**kw)],q(discount_pct=10,promotion_start='2026-01-01',promotion_end='2026-01-03'))['recommendation']['price']=='100.00'

def test_missing_competitor_and_simulation():
    assert evaluate([row()],q(mode='competitive_simulation'))['status']=='insufficient_evidence'
    assert evaluate([row(competitor_price='95')],q(mode='competitive_simulation'))['recommendation']['price']=='94.99'

def test_scarcity_and_cap_conflict():
    assert evaluate([row(stockout_risk=True,daily_demand=2,forecast_daily_demand=3)],q())['recommendation']['price']=='105.00'
    assert evaluate([row(unit_cost='200')],q())['status']=='insufficient_evidence'

def test_dates_empty_and_duplicate():
    assert evaluate([],q())['status']=='not_found'
    assert evaluate([row(observed_on='2026-02-01')],q())['status']=='not_found'
    with pytest.raises(ValueError):evaluate([row(),row()],q())
    with pytest.raises(ValidationError):q(promotion_start='2026-01-01')
    with pytest.raises(ValidationError):q(min_margin=1)
    with pytest.raises(ValidationError):row(current_price='NaN')

def test_currency_rounding_preserves_change_cap():
    result=evaluate([row(stockout_risk=True,daily_demand=2,forecast_daily_demand=3)],q(max_change_pct='0.005'))
    assert result['recommendation']['price']=='100.00'
