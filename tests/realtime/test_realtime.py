import asyncio,hashlib,hmac,json,time
from datetime import date,datetime,timezone,timedelta
import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from app.realtime.config import RealtimeSettings
from app.realtime.connectors.open_meteo import OpenMeteo
from app.realtime.stream.simulator import events
from app.realtime.stream.ingest import Event,Ingestor
from app.realtime.data import SalesEvent,WeatherHourly
from app.realtime.features_online import online
from app.realtime.service import install,store_weather
from app.enterprise import imports
from tests.phase3.test_imports import small_sales
from app.services.database_service import Database
from app.api.schemas import RequestContext
from app.security.policy import Grant,AccessDenied
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.main import create_app


@pytest.fixture
def database(tmp_path,monkeypatch):
    db=Database('sqlite:///'+str(tmp_path/'db'));source=tmp_path/'source.xlsx';source.write_bytes(b'fixture')
    monkeypatch.setattr(imports,'sheets',lambda *a:small_sales());imports.import_sales(db,source)
    for table in (SalesEvent.__table__,WeatherHourly.__table__):table.create(db.engine,checkfirst=True)
    yield db
    db.close()


def test_weather_offline_cache_and_fallback():
    calls=[]
    def transport(request):
        calls.append(request)
        if len(calls)>1:raise httpx.ConnectError('offline')
        return httpx.Response(200,json={'hourly':{'time':['2026-10-22T00:00'],'temperature_2m':[25.0],'precipitation':[0.0],'weather_code':[0]}})
    now=datetime(2026,10,22,tzinfo=timezone.utc)
    client=OpenMeteo(RealtimeSettings(_env_file=None,weather_enabled=True),transport=httpx.MockTransport(transport))
    result=asyncio.run(client.fetch(now=now));assert result['status']=='fresh'
    assert asyncio.run(client.fetch(now=now+timedelta(minutes=59)))['status']=='cached'
    assert len(calls)==1
    assert asyncio.run(client.fetch(now=now+timedelta(hours=2)))['status']=='stale_fallback'
    assert set(calls[0].url.params)=={'latitude','longitude','hourly','timezone','forecast_days','past_days'}
    disabled=OpenMeteo(RealtimeSettings(_env_file=None),transport=httpx.MockTransport(transport))
    assert asyncio.run(disabled.fetch())['status']=='disabled'
    bad=OpenMeteo(RealtimeSettings(_env_file=None,weather_enabled=True,weather_url='http://127.0.0.1/private'))
    with pytest.raises(ValueError):asyncio.run(bad.fetch())


def test_simulator_ingest_scope_and_late_events(database):
    rows=small_sales()['Sales_Transactions'];start=datetime(2026,1,1,tzinfo=timezone.utc)
    stream=list(events(rows,seed=42,start=start,count=3))
    assert stream==list(events(rows,seed=42,start=start,count=3)) and all(e.synthetic for e in stream)
    ingest=Ingestor(database);admin=RequestContext(session_id='s',principal_id='p',role='ADMIN')
    assert ingest.ingest(stream[2],admin)['status']=='inserted'
    assert ingest.ingest(stream[0],admin)['status']=='inserted'
    assert ingest.ingest(stream[0],admin)['status']=='duplicate'
    other=RequestContext(session_id='s',principal_id='p',role='STORE_MANAGER',store_ids=['outside'])
    with pytest.raises(AccessDenied):ingest.ingest(stream[1],other)
    changed=stream[0].model_copy(deep=True);changed.payload['color']='changed'
    with pytest.raises(ValueError):ingest.ingest(changed,admin)
    now=datetime.now(timezone.utc)
    assert online([],now)['units_1hour'] is None
    future_arrival=[{'occurred_at':now,'received_at':now+timedelta(seconds=1),'quantity':10}]
    assert online(future_arrival,now)['units_1hour'] is None


def test_api_signatures_and_scoped_stream(database,tmp_path):
    token='x'*40;other='y'*40;key='k'*40
    grants=[Grant(token_sha256=hashlib.sha256(t.encode()).hexdigest(),principal_id=t[:1],role=role,store_ids=stores) for t,role,stores in [(token,'ADMIN',[]),(other,'STORE_MANAGER',['outside'])]]
    cfg=RuntimeSettings(_env_file=None,database_url=SecretStr(str(database.engine.url)),state_dir=tmp_path/'runtime')
    api=create_app(cfg,runtime_factory=lambda db,c:Runtime(db,c,grants=grants))
    install(api,RealtimeSettings(_env_file=None,stream_mode='webhook',stream_hmac_key=SecretStr(key)))
    event=list(events(small_sales()['Sales_Transactions'],seed=42,start=datetime(2026,1,1,tzinfo=timezone.utc),count=1))[0].model_dump()
    event['synthetic']=False;body=json.dumps(event).encode();stamp=str(int(time.time()))
    headers={'Authorization':'Bearer '+token,'X-Event-Timestamp':stamp,'X-Event-Signature':hmac.new(key.encode(),stamp.encode()+b'.'+body,hashlib.sha256).hexdigest()}
    with TestClient(api) as client:
        assert client.get('/health').status_code==200
        assert client.get('/api/realtime/status').status_code==401
        assert client.post('/api/stream/ingest',content=body,headers={**headers,'X-Event-Signature':'bad'}).status_code==401
        assert client.post('/api/stream/ingest',content=body,headers=headers).json()['status']=='inserted'
        assert client.post('/api/stream/ingest',content=body,headers=headers).json()['status']=='duplicate'
        assert 'pos-webhook' in client.get('/api/stream/sales?once=true',headers=headers).text
        assert 'pos-webhook' not in client.get('/api/stream/sales?once=true',headers={'Authorization':'Bearer '+other}).text
        assert client.get('/api/realtime/status',headers={'Authorization':'Bearer '+other}).json()['latest_event'] is None


def test_incomplete_simulator_payload_reports_failure_without_task_crash(database, monkeypatch):
    from app.enterprise.data import Sale
    from app.realtime.service import Realtime
    from sqlalchemy import select
    with database.session() as session:
        for row in session.scalars(select(Sale)):
            row.payload = {'sale_date': '2026-01-01'}
    service = Realtime(database, RealtimeSettings(_env_file=None, stream_mode='simulator'))
    calls = []
    async def stop_after_two_iterations(delay):
        calls.append(service.task_status)
        if len(calls) == 2:
            raise asyncio.CancelledError()
    monkeypatch.setattr('app.realtime.service.asyncio.sleep', stop_after_two_iterations)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(service.run())
    assert calls == ['failed_iteration', 'failed_iteration']
    assert service.rows(RequestContext(session_id='test', principal_id='test', role='ADMIN'), 0) == []
