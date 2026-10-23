"""Run baseline parity and validation only; final-test access is deliberately excluded."""
import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import random
import sqlite3
import subprocess
from app.api.schemas import RequestContext
from app.services.database_service import Database
from app.conversation.forecast import backtest
from app.ml.features import daily_series
from app.ml.models import Baseline
from app.ml.evaluation import legacy_parity, rolling_origin
from app.ml.registry import fingerprint, save


def run(config: dict) -> dict:
    random.seed(config['seed'])
    cutoff=date.fromisoformat(config['cutoff']); test_start=date.fromisoformat(config['test_start'])
    if cutoff>=test_start:
        raise ValueError('Baseline development cannot access final-test dates')
    source=Path(config['database']).resolve()
    if not source.is_file():
        raise ValueError('Import the source workbooks first; no invented fallback dataset')
    with sqlite3.connect(f'file:{source.as_posix()}?mode=ro',uri=True) as connection:
        receipts=[json.loads(row[0]) for row in connection.execute("SELECT report FROM poc_imports WHERE domain='sales'")]
    if len(receipts)!=1 or not receipts[0].get('synthetic'):
        raise ValueError('This baseline configuration requires one labelled synthetic sales import')
    database=Database('sqlite:///'+source.as_posix())
    try:
        # Trusted local CLI authority; no web client can choose this role.
        context=RequestContext(session_id='offline-ml',principal_id='local-training',role='ADMIN')
        series=daily_series(database,context,cutoff,config['level'])
    finally:
        database.close()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    results=[]; origins=[date.fromisoformat(d) for d in config['origins']]
    for key,(days,values) in series.items():
        try:
            parity=legacy_parity(days,values)
        except ValueError:
            results.append({'series':list(key),'status':'INSUFFICIENT_COVERAGE'}); continue
        assert parity==backtest(days,values), 'Baseline numerical parity failed'
        for entry in parity:
            name=entry['model']; validations={str(h):rolling_origin(days,values,lambda:Baseline(name),origins,h,test_start=test_start) for h in config['horizons']}
            results.append({'series':list(key),'model':name,'parity':entry,'validation':validations,'status':'VALIDATION_ONLY'})
    record={'schema':1,'config':config,'config_hash':fingerprint(config),'source_hash':receipts[0]['sha256'],
            'source_label':'synthetic-workbook','code_commit':commit,'seed':config['seed'],
            'training_data_hash':fingerprint([[list(k),[d.isoformat() for d in days],values] for k,(days,values) in series.items()]),
            'date':datetime.now(timezone.utc).isoformat(),'final_test_opened':False,'results':results}
    output=Path(config['output']);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(record,indent=2,allow_nan=False),encoding='utf-8')
    log=Path('experiments/log.jsonl');log.parent.mkdir(exist_ok=True)
    with log.open('a',encoding='utf-8') as stream:
        for row in results:
            stream.write(json.dumps({k:v for k,v in record.items() if k!='results'}|{'result':row},allow_nan=False)+'\n')
    for key,(days,values) in series.items():
        matching=[r for r in results if r['series']==list(key) and 'model' in r]
        for row in matching:
            model=Baseline(row['model']).fit(days,values)
            identifier=fingerprint([record['source_hash'],config['level'],list(key),config['cutoff'],row['model'],commit])
            artifact=Path(config['registry'])/(identifier+'.json')
            if not artifact.exists():
                save(artifact,model,source_hash=record['source_hash'],features=['observed_units'],metrics={'parity':row['parity'],'label':'validation_only'},commit=commit)
    return record


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);args=parser.parse_args()
    # JSON is a strict YAML subset, keeping the baseline runner dependency-free.
    config=json.loads(args.config.read_text(encoding='utf-8'))
    result=run(config)
    print(f"Baseline run saved: {config['output']}; {len(result['results'])} results; final test unopened.")


if __name__=='__main__':main()
