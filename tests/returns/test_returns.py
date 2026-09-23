import pytest
from pydantic import ValidationError
from app.agents.returns.domain import ReturnRecord,Query,evaluate,categorize_reason

def r(**kw):return ReturnRecord(**dict(dict(store_id='s',order_id='o',observed_on='2026-01-01',delivered_on='2026-01-01',purchased_units=3,paid_total='100',policy=dict(window_days=30,allowed_reasons=['defect','wrong_item','change_of_mind'],receipt_required=True,allow_opened=False,source='fixture://policy'),source='fixture://order',fixture=True),**kw))
def q(**kw):return Query(**dict(dict(store_id='s',order_id='o',as_of='2026-01-31',reason='defect',has_receipt=True),**kw))

def test_inclusive_window_and_amount():
    result=evaluate([r()],q())
    assert result['eligible'] and result['advisory_refund_amount']=='33.33'
    assert not result['refund_executed']
    assert not evaluate([r()],q(as_of='2026-02-01'))['eligible']

@pytest.mark.parametrize('kw',[{'has_receipt':False},{'opened':True},{'reason':'other'},{'units_requested':4}])
def test_policy_rules(kw):assert not evaluate([r()],q(**kw))['eligible']

def test_missing_policy_order_and_refund():
    assert evaluate([],q())['status']=='not_found'
    assert evaluate([r(policy=None)],q())['eligible'] is None
    assert evaluate([r()],q(mode='refund_status'))['refund_status'] is None
    assert evaluate([r(refund_status='paid',refunded_total='20')],q(mode='refund_status'))['recorded_refunded_total']=='20'

def test_refund_cap_and_flags():
    result=evaluate([r(refunded_total='90',prior_return_count=5)],q(serial_mismatch=True))
    assert result['advisory_refund_amount']=='10.00'
    assert len(result['risk_review_flags'])==2 and result['requires_human']

def test_validation_and_duplicates():
    with pytest.raises(ValidationError):r(refunded_total='101')
    with pytest.raises(ValidationError):r(previously_returned_units=4)
    with pytest.raises(ValidationError):q(units_requested=0)
    with pytest.raises(ValueError):evaluate([r(),r()],q())

def test_taxonomy_and_delivery_absence():
    assert categorize_reason('Received the wrong item')=='wrong_item'
    assert categorize_reason('The product is broken')=='defect'
    assert categorize_reason('I changed my mind')=='change_of_mind'
    assert not evaluate([r(delivered_on=None)],q())['eligible']
