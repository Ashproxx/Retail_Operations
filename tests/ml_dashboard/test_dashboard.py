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
