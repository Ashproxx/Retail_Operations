from datetime import date,timedelta
import numpy as np
import pytest
from app.auxiliary.seasonal import compare


def series():
    dates=[date(2026,1,1)+timedelta(days=i) for i in range(146)]
    values=np.array([100+20*(i%7)+i%3 for i in range(146)],dtype=float)
    return dates,values


def test_stl_train_only_and_inputs_unchanged():
    dates,values=series();original=values.copy()
    result=compare(dates,values)
    changed=values.copy();changed[-56:]*=3
    other=compare(dates,changed)
    assert np.array_equal(values,original)
    assert result['train_days']==90 and result['validation_days']==56
    assert result['injected_days']==5
    for name in result['results']:
        assert result['results'][name]['threshold']==other['results'][name]['threshold']
        assert sum(map(sum,result['results'][name]['confusion_labels_0_1']))==56


def test_reject_gaps_and_final_test_dates():
    dates,values=series()
    with pytest.raises(ValueError,match='Contiguous'):compare(dates[1::2],values[1::2])
    with pytest.raises(ValueError,match='final-test'):compare(dates+[date(2026,5,27)],np.append(values,100))
    with pytest.raises(ValueError,match='nonnegative'):compare(dates,np.full(146,-1))
    with pytest.raises(ValueError,match='variable'):compare(dates,np.ones(146))
