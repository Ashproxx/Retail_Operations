from datetime import date,timedelta
from app.conversation.forecast import forecast, backtest
from app.conversation.contracts import Context


def test_forecast_uses_only_history_before_origin_and_shared_folds():
    start=date(2026,1,1)
    rows=[{'date':(start+timedelta(days=i)).isoformat(),'store_id':'A','sku_id':'P',
           'units_sold':10+i%7,'closing_stock':50,'source':'fixture','fixture':True} for i in range(60)]
    ctx=Context(store_id='A',period={'start':'2026-01-01','end':'2026-02-28','label':'February','timezone':'Asia/Kolkata'})
    a=forecast(rows,ctx)
    rows[-1]['units_sold']=999999
    assert forecast(rows,ctx)==a
    assert len(a['forecast'])==7
    assert a['model']==min(a['validation'],key=lambda x:(x['mae'],x['rmse'],x['model']))['model']
    assert len({m['evaluated_points'] for m in a['validation']})==1
    assert all(f['training_end']<f['target'] for m in a['validation'] for f in m['folds'])
    assert 'seasonal_naive_7' in [m['model'] for m in a['validation']]


def test_missing_days_and_zero_wape_are_honest():
    days=[date(2026,1,1)+timedelta(days=i) for i in range(21)]
    assert all(x['wape'] is None for x in backtest(days,[0]*21))
    ctx=Context(period={'start':'2026-01-01','end':'2026-01-21','label':'test','timezone':'Asia/Kolkata'})
    assert forecast([],ctx)['status']=='insufficient_data'
