from fastapi.testclient import TestClient
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.showcase import showcase_app

TOKEN = 'synthetic-browser-test-token-123456789'


def test_showcase_is_authenticated_and_uses_disposable_fixtures(tmp_path, monkeypatch):
    # Existing user configuration must not be loaded or overwritten.
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.env').write_text('RETAILOPS_DATABASE_URL=sqlite:///untouched.db\n')
    before = (tmp_path / '.env').read_bytes()
    (tmp_path / 'demo').mkdir()
    with TestClient(showcase_app(tmp_path / 'demo', TOKEN)) as client:
        page = client.get('/dashboard')
        assert page.status_code == 200
        assert "frame-ancestors 'none'" in page.headers['content-security-policy']
        assert client.get('/dashboard-assets/app.js').status_code == 200
        assert client.get('/api/inventory/BANDRA').status_code == 401
        headers = {'Authorization': 'Bearer ' + TOKEN}
        response = client.get('/api/inventory/BANDRA?as_of=2026-09-22', headers=headers).json()
        assert response['data']['fixture'] is True
        assert len(response['data']['results']['inventory']['data']['items']) == 6
        analytics = client.get('/api/analytics/summary?start=2026-09-09&end=2026-09-22', headers=headers).json()
        assert set(analytics['data']['results']['analytics-reporting']['data']['sales_by_store']) == {'BANDRA', 'ANDHERI', 'POWAI'}
        forecast = client.post('/api/query', headers=headers, json={'agent': 'demand-forecasting',
            'session_id': 'browser-test', 'parameters': {'store_id': 'BANDRA', 'sku_id': 'SHIRT-1', 'as_of': '2026-09-22'}}).json()
        assert len(forecast['data']['results']['demand-forecasting']['data']['forecast']) == 7
    assert (tmp_path / '.env').read_bytes() == before
    assert not (tmp_path / 'untouched.db').exists()


def test_normal_dashboard_never_seeds_data(tmp_path):
    config = RuntimeSettings(_env_file=None, database_url='sqlite:///' + str(tmp_path / 'normal.db'),
                             state_dir=tmp_path / 'state', grants_file=None)
    with TestClient(create_app(config)) as client:
        assert client.get('/dashboard').status_code == 200
        assert client.get('/').json()['stage'] == 'integration-candidate'
        assert client.get('/api/analytics/summary').status_code == 401
        from sqlalchemy import text
        with client.app.state.database.engine.connect() as connection:
            assert connection.execute(text('SELECT count(*) FROM domain_records')).scalar() == 0

