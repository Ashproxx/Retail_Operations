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
    from app.realtime.service import install as install_realtime
    from app.realtime.config import RealtimeSettings
    install_realtime(app,RealtimeSettings(_env_file=None))
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


def test_combined_live_scope_cursor_and_missingness(dashboard):
    from datetime import datetime, timezone
    from app.realtime.data import SalesEvent
    client,headers,_=dashboard
    now=datetime.now(timezone.utc).isoformat()
    with client.app.state.database.session() as session:
        for i in range(105):
            session.add(SalesEvent(txn_id=str(i),store_id='S1' if i%2 else 'S2',
                occurred_at=now,received_at=now,quantity=1,synthetic=True,
                source='integration-fixture',digest=str(i),payload={}))
    for role in ['STORE_MANAGER','ANALYST']:
        response=client.get('/api/realtime/status',headers=headers(role))
        assert response.headers['cache-control']=='no-store'
        assert response.json()['features']['units_1hour']==52
        assert response.json()['weather']['values'] is None
        response=client.get('/api/stream/sales?once=true',headers=headers(role))
        rows=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        assert len(rows)==52 and {r['store_id'] for r in rows}=={'S1'}
        assert client.get('/api/stream/sales?once=true&after='+str(rows[-1]['id']),headers=headers(role)).text==''
        assert client.get('/api/ml/results',headers=headers(role)).json()['live']['connected'] is True
    assert client.get('/api/stream/sales?once=true',headers=headers('ADMIN')).text.count('data: ')==100
    for path in ['/api/realtime/status','/api/stream/sales?once=true']:
        assert client.get(path,headers=headers('HR_ADMIN')).status_code==403
        assert client.get(path).status_code==401


@pytest.mark.parametrize('expired',[False,True])
def test_combined_routes_recheck_revocation_and_expiry(dashboard,expired):
    from datetime import datetime, timezone, timedelta
    from app.security.policy import TokenAuthenticator
    client,headers,_=dashboard
    auth=client.app.state.runtime.auth
    grants=list(auth._grants)
    for grant in grants:
        grant.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)
    client.app.state.runtime.auth=TokenAuthenticator(grants if expired else [])
    for path in ['/api/ml/results','/api/realtime/status','/api/stream/sales?once=true']:
        assert client.get(path,headers=headers('STORE_MANAGER')).status_code==401


def test_review_questions_share_scoped_evidence_with_assistant(dashboard):
    from app.ml_dashboard.answers import QUESTIONS
    client, headers, _ = dashboard
    answers = client.get('/api/ml/results', headers=headers('STORE_MANAGER')).json()['review_answers']
    assert len(answers) == 6
    for i, question in enumerate(QUESTIONS):
        response = client.post('/api/conversation', headers=headers('STORE_MANAGER'),
                               json={'session_id': 'ml-review', 'message': question})
        assert response.status_code == 200
        result = response.json()
        assert result['summary'] == answers[i]['summary']
        assert result['warnings'] and result['model'] and result['interval']
        assert result['operational_write_performed'] is False
        assert 'S2' not in response.text and 'private' not in response.text
        denied = client.post('/api/conversation', headers=headers('HR_ADMIN'),
                             json={'session_id': 'ml-review', 'message': question})
        assert denied.status_code == 403
    assert 'unknown' in answers[2]['summary']
    assert answers[2]['evidence']['features']['units_1hour'] is None
    assert 'causal' in answers[1]['summary']
    assert 'did not beat' in answers[4]['summary']


def test_review_answer_fails_closed_for_missing_evidence(dashboard):
    from app.ml_dashboard.answers import QUESTIONS
    client, headers, root = dashboard
    (root/'forecast.json').write_text('{}')
    result = client.post('/api/conversation', headers=headers('ADMIN'),
                         json={'session_id': 'ml-review', 'message': QUESTIONS[0]})
    assert result.status_code == 503
    assert client.post('/api/conversation', json={'session_id': 'x', 'message': QUESTIONS[0]}).status_code == 401


def test_review_answer_uses_scoped_frozen_comparison(dashboard):
    from app.ml_dashboard.answers import QUESTIONS
    client, headers, root = dashboard
    report = json.loads((root/'forecast.json').read_text())
    report['decisions'] = [dict(series=['store', store], horizon=28, candidate='candidate',
                               baseline='baseline', test_wape=.2, baseline_test_wape=.1)
                           for store in ['S1', 'S2']]
    raw = json.dumps(report).encode()
    (root/'forecast.json').write_bytes(raw)
    manifest = json.loads((root/'manifest.json').read_text())
    manifest['forecast.json']['sha256'] = hashlib.sha256(raw).hexdigest()
    (root/'manifest.json').write_text(json.dumps(manifest))
    result = client.post('/api/conversation', headers=headers('STORE_MANAGER'),
                         json={'session_id': 'comparison', 'message': QUESTIONS[0]}).json()
    assert '20.0000%' in result['summary'] and '+10.0000' in result['summary']
    assert len(result['evidence']['store_comparisons']) == 1
    assert 'S2' not in json.dumps(result)
