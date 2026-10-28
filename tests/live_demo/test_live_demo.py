from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
import hashlib
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.live_demo.config import Config, TZ, UTC, factors, instant, rng, sample
from app.live_demo.store import append, balance, connect, initialize, state
from app.live_demo.worker import correct, run_once
from app.live_demo.__main__ import import_records

DAY=date(2026,1,1)
NOW=instant(DAY+timedelta(days=3),20)


@pytest.fixture
def demo(tmp_path):
    path=tmp_path/'demo.db'
    initialize(path,config=Config(start_date=DAY,opening_units=3,reorder_at=2,delivery_units=5),now=NOW)
    return path


def event_rows(path):
    with connect(path) as db:
        return [tuple(r) for r in db.execute('SELECT id,digest,quantity,stock_delta,net_paise,occurred_at FROM demo_events ORDER BY id')]


def test_repeat_init_replay_restart_and_projection(demo):
    run_once(demo,now=NOW)
    before=event_rows(demo)
    assert initialize(demo,now=NOW)['status']=='already_initialized'
    assert run_once(demo,now=NOW)['accepted']==0
    assert event_rows(demo)==before
    with connect(demo) as db:
        assert db.execute('SELECT SUM(net_paise),SUM(quantity) FROM sales_transactions').fetchone()[:]==db.execute("SELECT SUM(net_paise),SUM(quantity) FROM demo_events WHERE kind IN('sale','return','damaged_return','reversal')").fetchone()[:]
        assert balance(db,'DEMO1','DEMO-SKU',NOW.isoformat())>=0
        assert db.execute('SELECT COUNT(*) FROM demo_checkpoints').fetchone()[0]==40


def test_crash_partial_batch_retry_matches_clean_run(demo,tmp_path):
    with pytest.raises(RuntimeError): run_once(demo,now=NOW,crash_after=1)
    with connect(demo) as db:
        assert db.execute('SELECT COUNT(*) FROM demo_checkpoints').fetchone()[0]==1
        assert db.execute("SELECT COUNT(*) FROM demo_runs WHERE status='failed'").fetchone()[0]==1
    run_once(demo,now=NOW)
    other=tmp_path/'other.db';initialize(other,config=Config(start_date=DAY,opening_units=3,reorder_at=2,delivery_units=5),now=NOW)
    run_once(other,now=NOW)
    assert event_rows(demo)==event_rows(other)


def test_two_workers_do_not_duplicate_slots(demo):
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda _:run_once(demo,now=NOW,max_slots=100),range(2)))
    assert sum(r['slots'] for r in results)==40
    with connect(demo) as db:
        assert db.execute('SELECT COUNT(*) FROM demo_checkpoints').fetchone()[0]==40


def test_backup_restore_resumes_without_duplicate_facts(demo,tmp_path):
    import subprocess
    import sys
    run_once(demo,now=NOW,max_slots=10)
    backup=tmp_path/'backup.db'
    command=[sys.executable,'-m','app.live_demo','backup','--database',str(demo),'--output',str(backup)]
    subprocess.run(command,check=True,capture_output=True)
    before=backup.read_bytes()
    assert subprocess.run(command,capture_output=True).returncode!=0
    assert backup.read_bytes()==before
    assert event_rows(backup)==event_rows(demo)
    # Resume the restored file and the original independently from the same committed checkpoint.
    run_once(backup,now=NOW);run_once(demo,now=NOW)
    assert event_rows(backup)==event_rows(demo)
    with connect(backup) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute('SELECT COUNT(*) FROM demo_checkpoints').fetchone()[0]==40


def test_backdated_second_opening_cannot_inflate_stock(demo,tmp_path):
    run_once(demo,now=NOW)
    before=event_rows(demo)
    file=tmp_path/'earlier-opening.json'
    file.write_text(json.dumps([{'identity':'earlier-opening','store':'DEMO1','sku':'DEMO-SKU',
                                'kind':'opening','quantity':100,'stock':100,
                                'at':instant(DAY-timedelta(days=1),10).isoformat()}]))
    with pytest.raises(ValueError,match='Opening balance already exists'): import_records(demo,file)
    assert event_rows(demo)==before


def test_independent_processes_catch_up_month_with_different_hash_seeds(demo,tmp_path):
    import os
    import subprocess
    import sys
    end=instant(DAY+timedelta(days=30),20)
    code='''
import sys
from datetime import datetime
from app.live_demo.worker import run_once
while run_once(sys.argv[1],now=datetime.fromisoformat(sys.argv[2]),max_slots=7)['slots']:
    pass
'''
    processes=[subprocess.Popen([sys.executable,'-c',code,str(demo),end.isoformat()],
                               env={**os.environ,'PYTHONHASHSEED':str(seed)},stdout=subprocess.PIPE,stderr=subprocess.PIPE)
               for seed in [3,29,97]]
    for process in processes:
        _,error=process.communicate(timeout=60)
        assert process.returncode==0,error.decode()
    reference=tmp_path/'reference.db'
    initialize(reference,config=Config(start_date=DAY,opening_units=3,reorder_at=2,delivery_units=5),now=end)
    run_once(reference,now=end,max_slots=1000)
    assert event_rows(demo)==event_rows(reference)
    with connect(demo) as db:
        assert db.execute('SELECT COUNT(*) FROM demo_checkpoints').fetchone()[0]==310
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute("SELECT MIN(stock) FROM (SELECT SUM(stock_delta) OVER(ORDER BY occurred_at,rowid) stock FROM demo_events)").fetchone()[0]>=0


def test_kolkata_midnight_and_no_future_completion(demo):
    now=instant(DAY,11)+timedelta(minutes=30)
    run_once(demo,now=now)
    with connect(demo) as db:
        assert db.execute('SELECT MAX(occurred_at) FROM demo_events').fetchone()[0]<=now.isoformat()
        assert db.execute("SELECT COUNT(*) FROM demo_attendance WHERE status='clock_out'").fetchone()[0]==0
        assert state(db,'next_slot')==instant(DAY,12).isoformat()
        assert db.execute('SELECT DISTINCT business_date FROM demo_events').fetchone()[0]==str(DAY)
    assert instant(DAY,0).date()==DAY-timedelta(days=1)
    with pytest.raises(ValueError): run_once(demo,now=now,through=DAY+timedelta(days=1))


def test_stock_conservation_returns_and_immutable_events(demo):
    run_once(demo,now=NOW)
    with connect(demo) as db:
        stock=0
        for row in db.execute('SELECT kind,quantity,stock_delta FROM demo_events ORDER BY occurred_at,rowid'):
            stock+=row['stock_delta'] or 0
            assert stock>=0
            if row['kind']=='sale': assert row['stock_delta']==-row['quantity']
            if row['kind']=='damaged_return': assert row['stock_delta']==0
        for sale in db.execute("SELECT * FROM demo_events WHERE kind='sale'"):
            returned=db.execute("SELECT -COALESCE(SUM(quantity),0) FROM demo_events WHERE original_id=? AND kind IN('return','damaged_return')",(sale['id'],)).fetchone()[0]
            assert returned<=sale['quantity']
        with pytest.raises(sqlite3.IntegrityError): db.execute('DELETE FROM demo_events')


def test_correction_retains_original_and_reconciles(demo):
    run_once(demo,now=NOW)
    with connect(demo) as db:
        sale=dict(db.execute("SELECT s.* FROM demo_events s WHERE kind='sale' AND NOT EXISTS(SELECT 1 FROM demo_events r WHERE r.original_id=s.id) ORDER BY rowid LIMIT 1").fetchone())
        original_total=db.execute('SELECT SUM(net_paise) FROM sales_transactions').fetchone()[0]
    correct(demo,sale['id'],reason='Test reversal',actor='test',now=NOW)
    with connect(demo) as db:
        assert db.execute('SELECT SUM(net_paise) FROM sales_transactions').fetchone()[0]==original_total-sale['net_paise']
        assert db.execute('SELECT COUNT(*) FROM demo_events WHERE id=?',(sale['id'],)).fetchone()[0]==1
        assert db.execute("SELECT COUNT(*) FROM demo_events WHERE kind='reversal'").fetchone()[0]==1
    with pytest.raises(ValueError): correct(demo,sale['id'],reason='Different reason',actor='test',now=NOW)
    replay=correct(demo,sale['id'],reason='Test reversal',actor='test',now=NOW)
    with connect(demo) as db:
        result=db.execute('SELECT accepted,skipped FROM demo_runs WHERE id=?',(replay['run_id'],)).fetchone()
        assert tuple(result)==(0,1)


def test_fresh_process_initializes_website_schema_before_writer(tmp_path):
    import subprocess
    import sys
    path=tmp_path/'fresh.db'
    code='''
import sys
from app.live_demo.store import initialize,connect
initialize(sys.argv[1])
from app.main import create_app
from app.models.database import Base
create_app()
with connect(sys.argv[1],write=True) as db:
    tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(Base.metadata.tables)<=tables
'''
    subprocess.run([sys.executable,'-c',code,str(path)],check=True,capture_output=True)


def test_import_duplicates_conflicts_and_failure_log(demo,tmp_path):
    file=tmp_path/'events.json'
    record={'identity':'opening','store':'DEMO1','sku':'DEMO-SKU','kind':'opening','quantity':5,'stock':5,'at':instant(DAY,10).isoformat()}
    file.write_text(json.dumps([record]))
    assert import_records(demo,file)['accepted']==1
    assert import_records(demo,file)['skipped']==1
    record['quantity']=record['stock']=6;file.write_text(json.dumps([record]))
    with pytest.raises(ValueError): import_records(demo,file)
    with connect(demo) as db:
        assert balance(db,'DEMO1','DEMO-SKU')==5
        assert db.execute("SELECT COUNT(*) FROM demo_runs WHERE status='failed'").fetchone()[0]==1


def test_bad_foreign_key_and_overreturn_roll_back(demo):
    run_once(demo,now=NOW)
    with connect(demo,write=True) as db:
        sale=db.execute("SELECT * FROM demo_events WHERE kind='sale' LIMIT 1").fetchone()
        with pytest.raises(ValueError): append(db,run_id=sale['run_id'],source='test',identity='too-many',store='DEMO1',sku='DEMO-SKU',
            kind='return',quantity=-sale['quantity']-1,stock=sale['quantity']+1,net=-1,original=sale['id'],at=NOW,received=NOW)
        with pytest.raises(sqlite3.IntegrityError): append(db,run_id=sale['run_id'],source='test',identity='missing',store='missing',sku='DEMO-SKU',
            kind='lost',quantity=1,at=NOW,received=NOW)


def test_seasonal_means_and_repeated_samples():
    cfg=Config(start_date=DAY,monthly={'Known':[1,1,1,2,1,1,1,1,1,1,1,1]},weekday=[1]*7,annual_trend=0)
    assert factors(cfg,date(2026,4,1),'Known')['combined']==2
    assert factors(cfg,date(2026,4,1),'Other')['combined']==1
    low=sum(sample(cfg,.5,rng(cfg,'low',i)) for i in range(2000))
    high=sum(sample(cfg,1,rng(cfg,'high',i)) for i in range(2000))
    assert 1.6<high/low<2.4
    with pytest.raises(ValueError): Config(weekday=[float('nan')]*7)


def test_source_snapshot_unchanged_and_staff_not_copied(demo,tmp_path):
    run_once(demo,now=NOW)
    # A reviewed source for this test contains only positive sales (no return projection).
    with connect(demo,write=True) as db: db.execute('DELETE FROM sales_transactions WHERE quantity<=0')
    before=hashlib.sha256(demo.read_bytes()).hexdigest()
    copy=tmp_path/'copy.db';initialize(copy,demo,Config(start_date=DAY-timedelta(days=2)),now=NOW)
    run_once(copy,now=NOW)
    assert hashlib.sha256(demo.read_bytes()).hexdigest()==before
    with connect(copy) as db:
        lo,hi=state(db,'imported_range')
        assert db.execute("SELECT COUNT(*) FROM demo_events WHERE synthetic=1 AND business_date BETWEEN ? AND ?",(lo,hi)).fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM employees').fetchone()[0]==3
    with pytest.raises(ValueError): initialize(demo,demo,now=NOW)


@pytest.fixture
def client(demo,tmp_path,monkeypatch):
    from app.main import create_app
    from app.integration.config import RuntimeSettings
    from app.integration.runtime import Runtime
    from app.security.policy import Grant
    from app.live_demo.routes import install
    monkeypatch.setattr('app.live_demo.routes.now_utc',lambda:NOW)
    monkeypatch.setattr('app.live_demo.datasets.now_utc',lambda:NOW)
    run_once(demo,now=NOW)
    tokens={r:r+'x'*40 for r in ['ADMIN','ANALYST','STORE_MANAGER','HR_ADMIN','HR_USER']}
    grants=[Grant(token_sha256=hashlib.sha256(t.encode()).hexdigest(),principal_id=r,role=r,store_ids=['outside'] if r=='STORE_MANAGER' else ['DEMO1']) for r,t in tokens.items()]
    api=create_app(RuntimeSettings(_env_file=None,email_login=False,database_url='sqlite:///'+str(demo),state_dir=tmp_path/'runtime'),runtime_factory=lambda db,c:Runtime(db,c,grants=grants))
    install(api,demo)
    with TestClient(api) as client: yield client,lambda r:{'Authorization':'Bearer '+tokens[r]}


def test_api_totals_staff_scope_cursor_export_and_unknown(client):
    client,headers=client
    response=client.get('/api/demo/summary',headers=headers('ADMIN'))
    assert response.status_code==200 and response.headers['cache-control']=='no-store'
    data=response.json();assert data['today']['units'] is not None
    assert data['source']=='all' and data['worker']=='worker-stopped'
    assert client.get('/api/demo/summary',headers=headers('HR_ADMIN')).status_code==403
    assert client.get('/api/demo/staff',headers=headers('ANALYST')).status_code==403
    assert client.get('/api/demo/staff',headers=headers('HR_ADMIN')).json()['rows']
    assert client.get('/api/demo/summary',headers=headers('STORE_MANAGER')).json()['totals']['units'] is None
    assert client.get('/api/demo/summary?store=DEMO1',headers=headers('STORE_MANAGER')).status_code==403
    first=client.get('/api/demo/events?limit=2',headers=headers('ANALYST')).json()
    second=client.get('/api/demo/events?limit=2&after='+str(first['next']),headers=headers('ANALYST')).json()
    assert {r['id'] for r in first['rows']}.isdisjoint({r['id'] for r in second['rows']})
    assert all('source' in r and 'received_at' in r and 'original_id' in r for r in first['rows'])
    assert client.get('/api/demo/runs',headers=headers('ANALYST')).status_code==403
    assert client.get('/api/demo/events').status_code==401


def test_arrival_cutoff_excludes_later_correction(client,demo):
    client,headers=client
    with connect(demo) as db: sale=db.execute("SELECT s.id FROM demo_events s WHERE kind='sale' AND NOT EXISTS(SELECT 1 FROM demo_events r WHERE r.original_id=s.id) LIMIT 1").fetchone()[0]
    correct(demo,sale,reason='Late correction',actor='test',now=NOW+timedelta(hours=1))
    data=client.get('/api/demo/events?limit=100&known_at='+NOW.isoformat().replace('+','%2B'),headers=headers('ADMIN')).json()
    assert all(r['kind']!='reversal' for r in data['rows'])


def test_landing_inventory_uses_movements_and_hr_attendance(client,demo,monkeypatch):
    client,headers=client
    response=client.get('/api/datasets/products',headers=headers('ADMIN'))
    assert response.status_code==200 and response.headers['cache-control']=='no-store'
    data=response.json()
    with connect(demo) as db: expected=balance(db,'DEMO1','DEMO-SKU',NOW.isoformat())
    assert data['metrics']['Known available units']==expected==sum(data['groups'].values())
    assert data['rows'][0]['available_units']==expected
    assert client.get('/api/datasets/products',headers=headers('STORE_MANAGER')).json()['rows']==[]
    assert client.get('/api/datasets/products',headers=headers('HR_USER')).status_code==403
    assert client.get('/api/datasets/employees',headers=headers('ANALYST')).status_code==403
    assert client.get('/api/datasets/employees',headers=headers('STORE_MANAGER')).status_code==403
    # Historical clock-outs already in storage must not change an earlier on-duty view.
    midday=instant(DAY,12)
    monkeypatch.setattr('app.live_demo.datasets.now_utc',lambda:midday)
    staff=client.get('/api/datasets/employees',headers=headers('HR_USER')).json()
    with connect(demo) as db:
        expected=db.execute("SELECT COUNT(*) FROM demo_attendance a JOIN demo_shifts s ON s.id=a.shift_id WHERE s.business_date=? AND a.status='clock_in' AND a.occurred_at<=?",(str(DAY),midday.isoformat())).fetchone()[0]
    assert staff['metrics']['On duty']==expected
    assert sum(staff['groups'].values())==staff['metrics']['Employees']
    assert all(r['store_id']=='DEMO1' for r in staff['rows'])
    assert not any(r['current_status']=='Finished' for r in staff['rows'])
