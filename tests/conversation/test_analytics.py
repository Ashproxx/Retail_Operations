from app.conversation.analytics import analyze
from app.conversation.contracts import Context
from app.conversation.taxonomy import normalize


def row(day, units, stock):
    return normalize(dict(date=day,store_id='A',store_location='Bandra',sku_id='P',category='shorts',units_sold=units,
        unit_price_inr='0.10',closing_stock=stock,reorder_point=2,source='fixture',fixture=True))


def test_exact_money_and_stock_constrained_not_low_demand():
    ctx=Context(intent='sales',store_id='A',location='Bandra',period={'start':'2026-09-28','end':'2026-09-28','label':'Today','timezone':'Asia/Kolkata'})
    result=analyze([row('2026-09-27',10,20),row('2026-09-28',3,0)],ctx)
    assert result['key_numbers']['revenue_inr']=='0.30'
    assert result['diagnostics'][0]['status']=='STOCK_CONSTRAINED'
    assert result['recommendations'][0]['executed'] is False
    assert 'replenishment' in result['recommendations'][0]['what']


def test_decline_requires_comparable_history_and_unknown_is_not_zero():
    ctx=Context(period={'start':'2026-09-28','end':'2026-09-28','label':'Today','timezone':'Asia/Kolkata'})
    assert analyze([row('2026-09-28',3,20)],ctx)['diagnostics'][0]['status']=='INSUFFICIENT_DATA'
    assert analyze([row('2026-09-27',10,20),row('2026-09-28',3,20)],ctx)['diagnostics'][0]['status']=='LOW_SALES'
    assert analyze([],ctx)['status']=='no_data'
