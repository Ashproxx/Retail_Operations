from datetime import date
import pytest
from app.auxiliary.evaluation import delivery_orders, delivery_evaluation, classification_metrics, product_segments, anomaly_evaluation


def order(**updates):
    row = dict(store_id='S', order_id='O', fulfillment_type='Home Delivery',
        sale_date='2026-03-01', promised_delivery_date='2026-03-03', actual_delivery_date='2026-03-04',
        delivery_status='Delivered', sales_channel='Web', delivery_partner='Fleet', quantity=2)
    return row | updates


def test_order_deduplication_and_no_outcome_features():
    orders, excluded = delivery_orders([order(), order()])
    assert not excluded and len(orders) == 1
    assert orders[0]['label'] == 1 and orders[0]['resolved'] == date(2026,3,4)
    assert orders[0]['x'] == ['S','Web','Fleet','6',2,4]


def test_inconsistent_and_unresolved_orders_are_not_negative_labels():
    orders, excluded = delivery_orders([order(), order(actual_delivery_date='2026-03-03'),
        order(order_id='B', delivery_status='In Process', actual_delivery_date=None)])
    assert orders == []
    assert excluded == {'inconsistent_order_lines':1, 'unresolved_or_missing_actual':1}


def test_invalid_order_chronology_and_nonfinite_units():
    assert delivery_orders([order(actual_delivery_date='2026-02-01')])[0] == []
    assert delivery_orders([order(quantity=float('nan'))])[0] == []


def test_metrics_calibration_and_single_class():
    result = classification_metrics([0,1], [0,1])
    assert result['roc_auc'] == 1 and result['brier'] == 0 and result['ece_10_bins'] == 0
    assert sum(b['count'] for b in result['calibration_bins']) == 2
    assert classification_metrics([0,0],[.2,.3])['roc_auc'] is None
    with pytest.raises(ValueError): classification_metrics([0],[float('nan')])
    with pytest.raises(ValueError): classification_metrics([2],[.2])


def test_missing_history_is_not_zero_filled():
    assert anomaly_evaluation([])['status'] == 'UNVERIFIED'
    assert product_segments([])['status'] == 'UNVERIFIED'


def test_delivery_labels_respect_partition_resolution_dates():
    rows=[]
    for month in ('03','05','09'):
        for i in range(6):
            rows.append(order(order_id=month+str(i), sale_date=f'2026-{month}-01',
                promised_delivery_date=f'2026-{month}-03',
                actual_delivery_date=f'2026-{month}-0{3+i%2}'))
    rows.append(order(order_id='late-label', sale_date='2026-03-31',
        promised_delivery_date='2026-04-01', actual_delivery_date='2026-04-02'))
    result=delivery_evaluation(rows)
    assert result['train_orders'] == 6
    assert result['excluded']['label_unavailable_at_partition_end'] == 1
    assert result['results']['test']['logistic']['n'] == 6
    assert result['results']['validation']['prevalence_baseline']['positive_rate'] == .5


def test_calibration_assigns_every_probability_once():
    p=[i/100 for i in range(101)]
    report=classification_metrics([i%2 for i in range(101)],p)
    assert sum(b['count'] for b in report['calibration_bins']) == 101
