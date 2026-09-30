from types import SimpleNamespace
from decimal import Decimal
import pytest
from app.api.schemas import RequestContext
from app.services.database_service import Database
from app.integration.repository import Repository
from app.conversation.catalog import Catalog, import_observations, ObservationRow
from app.conversation.ingest import load
from app.security.policy import AccessDenied
from sqlalchemy import select


def sample(**updates):
    return dict(date='2026-09-28',store_id='S1',store_location='Bandra',sku_id='P1',category='formal shirt',
                style_name='Oxford',units_sold=3,unit_price_inr='999.50',closing_stock=8,reorder_point=10,**updates)


def test_atomic_import_raw_product360_and_scoped_discovery(tmp_path):
    db=Database('sqlite:///'+str(tmp_path/'db'))
    repo=Repository(db)
    raw=sample()
    import_observations(db,[raw],source='fixture.csv',fixture=True,raw_sources=[{'Original price':'999.50'}])
    other={**raw,'store_id':'S2','store_location':'Private store','sku_id':'P2'}
    import_observations(db,[other],source='fixture.csv')
    ctx=RequestContext(session_id='x',principal_id='manager',role='STORE_MANAGER',store_ids=['S1'])
    catalog=Catalog(SimpleNamespace(repository=repo),ctx)
    rows=catalog.observations()
    assert catalog.discover('store_location',rows)==['Bandra']
    assert rows[0]['price_band']=='under_1000_inr'
    assert rows[0]['season_key']=='Monsoon'
    assert catalog.product360(rows,'P1')['performance']['revenue_inr']=='2998.50'
    assert rows[0]['raw_source']=={'Original price':'999.50'}
    assert catalog.product360(rows,'P1')['attributes']['style_name']=='Oxford'
    assert 'supplier' in catalog.product360(rows,'P1')['unknown_attributes']
    with pytest.raises(AccessDenied):catalog.observations('S2')
    with pytest.raises(ValueError):import_observations(db,[{**raw,'sku_id':'P3'},{**raw,'sku_id':'P4','units_sold':-1}],source='bad')
    assert len(catalog.observations())==1
    with pytest.raises(ValueError):import_observations(db,[raw],source='duplicate')
    db.close()


def test_csv_mapping_and_formula_rejection(tmp_path):
    path=tmp_path/'data.csv'
    path.write_text('when,location,code,item,units,price,stock,reorder\n2026-09-28,Bandra,S1,P1,2,100,3,5\n')
    mapping={'date':'when','store_location':'location','store_id':'code','sku_id':'item','units_sold':'units','unit_price_inr':'price','closing_stock':'stock','reorder_point':'reorder'}
    rows=load(path,mapping)
    assert rows[0][0]['units_sold']==2
    assert rows[0][1]['location']=='Bandra'
    path.write_text(path.read_text().replace(',100,',',=100,'))
    with pytest.raises(ValueError):load(path,mapping)
