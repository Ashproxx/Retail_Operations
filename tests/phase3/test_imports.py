from copy import deepcopy
import pytest
from sqlalchemy import select,func
from app.services.database_service import Database
from app.enterprise import imports
from app.enterprise.data import Sale,ImportBatch


def small_sales():
    row={k:None for k in imports.SALES_COLUMNS}
    row.update(txn_id='T1',order_id='O1',sale_date='2026-09-29',store_id='S1',city='Test City',store_location='Test City',sku_id='P1',category='Shirts',style_name='Oxford',quantity=1,unit_price_inr=1599,discount_pct=25,net_amount_inr=1199,sales_channel='Website')
    peer=dict(week_start='2026-09-28',store_id='S1',city='Test City',category='Shirts',competitor='Test peer',competitor_promo_active=0,competitor_avg_discount_pct=0,competitor_avg_price_inr=100,competitor_units_sold_est=5,competitor_revenue_est_inr=500,our_units_sold=1,our_revenue_inr=1199,our_share_of_tracked_market_pct=16.67)
    return {'Sales_Transactions':[row],'Competitor_Sales':[peer],'Store_Master':[dict(store_id='S1',city='Test City',store_area_sqft=1000)]}


def test_atomic_net_revenue_and_duplicate_import(tmp_path,monkeypatch):
    db=Database('sqlite:///'+str(tmp_path/'db'));path=tmp_path/'input.xlsx';path.write_bytes(b'fixture')
    data=small_sales();monkeypatch.setattr(imports,'sheets',lambda *a:data)
    report=imports.import_sales(db,path)
    assert report['net_revenue_inr']=='1199' and report['orders']==1
    assert imports.import_sales(db,path)['already_imported']
    path.write_bytes(b'changed');data=deepcopy(data);data['Sales_Transactions'][0].update(txn_id='T2',net_amount_inr=-1)
    with pytest.raises(ValueError):imports.import_sales(db,path)
    with db.session() as s:
        assert s.scalar(select(func.count()).select_from(Sale))==1
        assert s.scalar(select(func.count()).select_from(ImportBatch))==1
    db.close()


def test_numbers_and_date_validation():
    for value in ['NaN','Infinity',-1]:
        with pytest.raises(ValueError):imports.paise(value)
    with pytest.raises(ValueError):imports.integer(1.5)
    with pytest.raises(ValueError):imports.day('2026-02-30')
    with pytest.raises(ValueError):imports.identifier('../bad')
