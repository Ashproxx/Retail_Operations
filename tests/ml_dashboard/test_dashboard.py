import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.security.policy import Grant
from app.ml_dashboard.routes import install


@pytest.fixture
def dashboard(tmp_path):
    roles=['ADMIN','STORE_MANAGER','ANALYST','HR_ADMIN']
    tokens={role: role+'-test-token-'*4 for role in roles}
    grants=[Grant(token_sha256=hashlib.sha256(tokens[r].encode()).hexdigest(),principal_id=r,
                  role=r,store_ids=['S1']) for r in roles]
    app=create_app(RuntimeSettings(_env_file=None,database_url='sqlite:///'+str(tmp_path/'test.db'),
                                  state_dir=tmp_path/'state'),
                   runtime_factory=lambda db,cfg:Runtime(db,cfg,grants=grants))
    report=dict(source_label='synthetic-workbook',code_commit='fixture',
        curves=[{'series':s,'horizon':28} for s in [['chain','chain'],['store','S1'],['store','S2']]],
        decisions=[{'series':s,'horizon':28} for s in [['chain','chain'],['store','S1'],['store','S2']]],
        leaderboard=[{'global':'private'}],test_failures=[{'series':['store','S2']}],
        excluded_by_level={'store':9},limitations=['fixture only'])
    manifest={}
    for name,data in [('forecast.json',report),('auxiliary.json',{'private':'global'}),
                      ('supplement.json',{'importance':{'private':'chain-only'}})]:
        raw=json.dumps(data).encode();(tmp_path/name).write_bytes(raw)
        manifest[name]={'sha256':hashlib.sha256(raw).hexdigest()}
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    install(app,tmp_path)
    with TestClient(app) as client:
        yield client,lambda role:{'Authorization':'Bearer '+tokens[role]},tmp_path


def test_dashboard_shell_contains_no_results(dashboard):
    client,_,_=dashboard
    response=client.get('/ml')
    assert response.status_code==200 and "script-src 'self'" in response.headers['content-security-policy']
    assert 'S2' not in response.text
    assert client.get('/api/ml/results').status_code==401


@pytest.mark.parametrize('role',['STORE_MANAGER','ANALYST'])
def test_authorization_filters_every_series_and_global_aggregate(dashboard,role):
    client,headers,_=dashboard
    response=client.get('/api/ml/results',headers=headers(role))
    assert response.status_code==200 and response.headers['cache-control']=='no-store'
    data=response.json()
    assert [r['series'] for r in data['curves']]==[['store','S1']]
    assert [r['series'] for r in data['decisions']]==[['store','S1']]
    assert data['leaderboard']==[] and data['test_failures']==[]
    assert data['auxiliary'] is None and data['excluded_by_level'] is None
    assert data['supplement'] is None
    assert 'S2' not in response.text and 'private' not in response.text


def test_admin_and_hr_permissions(dashboard):
    client,headers,_=dashboard
    assert len(client.get('/api/ml/results',headers=headers('ADMIN')).json()['curves'])==3
    assert client.get('/api/ml/results',headers=headers('HR_ADMIN')).status_code==403
    assert client.get('/api/ml/results',headers=headers('ADMIN')).json()['supplement']['importance']['private']=='chain-only'


def test_corrupt_or_missing_evidence_fails_closed(dashboard):
    client,headers,root=dashboard
    (root/'forecast.json').write_text('{}')
    assert client.get('/api/ml/results',headers=headers('ADMIN')).status_code==503
    (root/'forecast.json').unlink()
    assert client.get('/api/ml/results',headers=headers('ADMIN')).status_code==503


def test_checksum_valid_malformed_rows_fail_closed(dashboard):
    client,headers,root=dashboard
    report=json.loads((root/'forecast.json').read_text())
    report['curves']=[None]
    raw=json.dumps(report).encode()
    (root/'forecast.json').write_bytes(raw)
    manifest=json.loads((root/'manifest.json').read_text())
    manifest['forecast.json']['sha256']=hashlib.sha256(raw).hexdigest()
    (root/'manifest.json').write_text(json.dumps(manifest))
    for role in ['ADMIN','STORE_MANAGER','ANALYST']:
        assert client.get('/api/ml/results',headers=headers(role)).status_code==503


def test_coverage_scopes_window_and_preserves_unknown_vs_zero(dashboard):
    from app.enterprise.data import Sale, Product
    from app.integration.repository import StoreRow
    client,headers,_=dashboard
    database=client.app.state.runtime.repository.database
    with database.session() as session:
        session.add_all([StoreRow(id='S1',name='One'),StoreRow(id='S2',name='Two'),
                         Product(sku_id='P',payload={})])
        session.flush()
        for i,(store,day,quantity) in enumerate([('S1','2026-03-01',0),
                                                ('S1','2026-03-03',5),('S2','2026-06-01',8)]):
            session.add(Sale(txn_id=str(i),order_id=str(i),store_id=store,sku_id='P',day=day,
                             category='fixture',channel='fixture',quantity=quantity,net_paise=0,payload={}))
    for role in ['STORE_MANAGER','ANALYST']:
        response=client.get('/api/ml/results',headers=headers(role))
        assert response.status_code==200
        quality=response.json()['data_quality']
        assert quality['end']=='2026-03-03'
        assert [s['store_id'] for s in quality['stores']]==['S1']
        row=quality['stores'][0]
        assert row['observed_days']==2 and row['unknown_days']==26
        assert row['units'][-3:]==[0,None,5]
    assert client.get('/api/ml/results',headers=headers('ADMIN')).json()['data_quality']['end']=='2026-06-01'


def test_empty_coverage_does_not_invent_zero(dashboard):
    client,headers,_=dashboard
    quality=client.get('/api/ml/results',headers=headers('STORE_MANAGER')).json()['data_quality']
    assert quality=={'status':'no_observations','start':None,'end':None,'stores':[]}
