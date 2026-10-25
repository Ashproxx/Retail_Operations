from datetime import date, timedelta
import math

import pytest
from app.auxiliary.price import price_association


def rows():
    result = []
    for i in range(90):
        day = date(2026, 1, 1) + timedelta(days=i)
        for sku, base in [('A', 2), ('B', 3)]:
            price = math.exp(base + .3 * math.sin(i * .7))
            units = math.exp(4 - .4 * math.log(price) + .02 * day.weekday() + .001 * i)
            result.append((day.isoformat(), sku, units, price * units))
    return result


def test_descriptive_coefficient_and_no_input_mutation():
    data = rows(); original = list(data)
    result = price_association(data)
    assert data == original
    assert result['log_price_coefficient'] == pytest.approx(-.4)
    assert result['observed_product_days'] == 180
    assert result['interval_degrees_of_freedom'] == result['week_clusters'] - 1
    assert result['cluster_week_t_interval_95'][0] <= -.4 + 1e-12
    assert result['cluster_week_t_interval_95'][1] >= -.4 - 1e-12


def test_no_zero_fill_and_unidentified_price():
    data = rows()
    incomplete = price_association(data[4:])
    assert incomplete['observed_product_days'] == len(data) - 4
    constant = [(d, sku, units, units * 10) for d, sku, units, _ in data]
    assert price_association(constant)['status'] == 'UNVERIFIED'


def test_reject_test_period_duplicates_and_invalid_values():
    data = rows()
    for extra, message in [(('2026-04-01', 'A', 1, 1), 'Training-only'),
                           (data[0], 'Unique'),
                           (('2025-12-31', 'A', 0, 1), 'Positive'),
                           (('2025-12-31', 'A', 1, float('nan')), 'Positive')]:
        with pytest.raises(ValueError, match=message):
            price_association(data + [extra])
