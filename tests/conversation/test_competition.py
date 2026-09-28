from types import SimpleNamespace
from app.conversation.competition import compare
from app.conversation.catalog import Catalog
from app.conversation.contracts import Context
from app.conversation.taxonomy import normalize


def test_only_observed_internal_family_candidates_and_missing_attributes():
    rows=[normalize(dict(date='2026-09-28',store_id='A',sku_id=str(i),store_location='Bandra',category=category,
                         style_name=name,unit_price_inr=str(price),units_sold=units,closing_stock=10,source='fixture',fixture=True))
          for i,category,name,price,units in [(1,'shirt','Oxford',100,2),(2,'formal shirt','Linen',110,5),(3,'shorts','Summer',90,8)]]
    catalog=object.__new__(Catalog)
    ctx=Context(sku_id='1',store_id='A',period={'start':'2026-09-28','end':'2026-09-28','label':'Today','timezone':'Asia/Kolkata'})
    result=compare(rows,ctx,catalog)
    assert [x['product'] for x in result['candidates']]==['Linen']
    assert result['candidates'][0]['outselling_target']
    assert result['candidates'][0]['observed_weight']<1
    assert 'not configured' in result['external_status']
    assert 'gender' not in result['candidates'][0]['factors']
