"""Explicit init/backfill/run-once/worker/status/launch/backup/correct/import commands."""
import argparse
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import time
from app.live_demo.config import TZ, UTC, digest, load
from app.live_demo.store import append, connect, initialize, new_run, now_utc, set_state, state
from app.live_demo.worker import correct, run_once


def import_records(path,file):
    raw=Path(file).read_bytes()
    if len(raw)>5_000_000: raise ValueError('Import exceeds 5 MB')
    now=now_utc()
    with connect(path,write=True) as db: run=new_run(db,'local-json-import',hashlib.sha256(raw).hexdigest(),now)
    try:
        rows=json.loads(raw)
        if not isinstance(rows,list) or len(rows)>5000: raise ValueError('Expected at most 5000 event objects')
        accepted=skipped=0
        with connect(path,write=True) as db:
            state(db,'config')
            for row in rows:
                if row.get('kind') not in {'opening','delivery','sale','return','damaged_return','adjustment'}:
                    raise ValueError('Unsupported import kind')
                identity=row.pop('identity');at=datetime.fromisoformat(row.pop('at'))
                if any(k in row for k in ['source','synthetic','run_id','received','actor']): raise ValueError('Provenance is server-owned')
                _,inserted=append(db,run_id=run,source='simulated-json-import',identity=identity,at=at,received=now,actor='local-operator',**row)
                accepted+=inserted;skipped+=not inserted
            db.execute("UPDATE demo_runs SET ended_at=?,status='success',accepted=?,skipped=? WHERE id=?",(now.isoformat(),accepted,skipped,run))
        return {'accepted':accepted,'skipped':skipped,'run_id':run}
    except Exception as exc:
        with connect(path,write=True) as db:
            db.execute("UPDATE demo_runs SET ended_at=?,status='failed',rejected=1,error=? WHERE id=?",(now.isoformat(),str(exc)[:200],run))
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['init','backfill','run-once','worker','status','launch','backup','correct','import'])
    parser.add_argument('--database',type=Path,default=Path('.retailops/live-demo/retailops.db'))
    parser.add_argument('--source',type=Path)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--start',type=date.fromisoformat)
    parser.add_argument('--months',type=int,choices=[24])
    parser.add_argument('--through',type=date.fromisoformat)
    parser.add_argument('--intraday',action='store_true')
    parser.add_argument('--interval',type=int,default=30)
    parser.add_argument('--max-slots',type=int,default=100)
    parser.add_argument('--port',type=int,default=8003)
    parser.add_argument('--role',choices=['ADMIN','ANALYST','STORE_MANAGER','HR_ADMIN','HR_USER'],default='ADMIN')
    parser.add_argument('--stores',nargs='*',default=[])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--file',type=Path)
    parser.add_argument('--event');parser.add_argument('--reason');parser.add_argument('--actor',default='local-operator')
    parser.add_argument('--replacement-units',type=int)
    args=parser.parse_args();path=args.database.resolve()
    if args.command=='init':
        config=load(args.config)
        start=args.start
        if args.months:
            today=now_utc().astimezone(TZ).date();start=date(today.year-2,today.month,1)
        if start: config=config.model_copy(update={'start_date':start})
        print(json.dumps(initialize(path,args.source,config),default=str));return
    with connect(path) as db: state(db,'config')
    if args.command=='launch':
        import uvicorn
        from app.main import create_app
        from app.integration.config import RuntimeSettings
        from app.integration.runtime import Runtime
        from app.security.policy import Grant
        from app.live_demo.routes import install
        from app.ml_dashboard.routes import install as review
        if args.role not in ['ADMIN','HR_ADMIN'] and not args.stores: parser.error('Scoped roles require --stores')
        token=secrets.token_urlsafe(32)
        grant=Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id='demo-operator',role=args.role,
                    store_ids=args.stores,expires_at=now_utc()+timedelta(hours=8))
        settings=RuntimeSettings(email_login=False,database_url='sqlite:///'+path.as_posix(),state_dir=path.parent/'runtime')
        api=create_app(settings,runtime_factory=lambda db,cfg:Runtime(db,cfg,grants=[grant]));install(api,path);review(api)
        print(f'SIMULATED DEMO DATA: http://127.0.0.1:{args.port}/models\nTemporary token (8 hours): {token}',flush=True)
        uvicorn.run(api,host='127.0.0.1',port=args.port);return
    if args.command=='backup':
        if not args.output or args.output.exists() or args.output.resolve()==path: parser.error('Choose a new backup path')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with connect(path) as db,sqlite3.connect(args.output) as backup: db.backup(backup)
        print('Consistent backup created');return
    if args.command=='status':
        with connect(path) as db:
            result={key:state(db,key) for key in ['config','next_slot','last_success','worker_heartbeat','imported_range']}
            result['counts']={table:db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ['sales_transactions','demo_events','employees','demo_shifts','demo_attendance','demo_runs']}
            print(json.dumps(result,indent=2))
        return
    if args.command=='correct':
        if not args.event or not args.reason: parser.error('--event and --reason required')
        print(json.dumps(correct(path,args.event,reason=args.reason,actor=args.actor,replacement_units=args.replacement_units)));return
    if args.command=='import':
        if not args.file: parser.error('--file required')
        print(json.dumps(import_records(path,args.file)));return
    if not 5<=args.interval<=3600: parser.error('Interval must be 5 to 3600 seconds')
    try:
        while True:
            now=now_utc()
            through=args.through or (None if args.intraday else now.astimezone(TZ).date()-timedelta(days=1))
            try:
                if args.command=='worker':
                    with connect(path,write=True) as db: set_state(db,'worker_heartbeat',now.isoformat())
                result=run_once(path,through=through,max_slots=args.max_slots)
            except sqlite3.OperationalError as exc:
                if args.command!='worker' or 'locked' not in str(exc).lower(): raise
                print('Another writer holds the database; retrying.',flush=True)
                time.sleep(args.interval);continue
            print(json.dumps(result),flush=True)
            if args.command=='run-once' or args.command=='backfill' and not result['slots']: break
            if args.command=='worker': time.sleep(args.interval)
    except KeyboardInterrupt: pass
    finally:
        if args.command=='worker':
            with connect(path,write=True) as db: set_state(db,'worker_heartbeat',None)


if __name__=='__main__': main()
