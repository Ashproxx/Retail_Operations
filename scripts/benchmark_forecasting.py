"""Two-stage frozen validation/test benchmark; no shuffled splits or zero-filled labels."""
import argparse,hashlib,json,subprocess,time
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
from statistics import mean
from app.api.schemas import RequestContext
from app.services.database_service import Database
from app.ml.features import daily_series,validate_series
from app.ml.models import Baseline
from app.ml.intermittent import Intermittent
from app.ml.forecasting import ForecastModel
from app.ml.evaluation import metrics,paired_bootstrap
from app.ml.intervals import intervals,interval_metrics
from app.ml.registry import fingerprint

BASELINES=['naive','moving_average_7','exponential_0.3','seasonal_naive_7','weekday_mean_28']
MODELS=BASELINES+['croston','sba','tsb','gamma_poisson','ets','sarima','sarimax_calendar','ridge','lasso','hist_gradient']
ORIGINS=[date(2026,3,31),date(2026,4,21),date(2026,5,12),date(2026,6,9)]
HORIZONS=[1,7,14,28]
LEVELS=['chain','store','store_category','store_sku']
TEST_START=date(2026,8,5)


def factory(name):
    return Baseline(name) if name in BASELINES else Intermittent(name) if name in ('croston','sba','tsb','gamma_poisson') else ForecastModel(name)


def implementation_hash():
    return fingerprint({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('app/ml').glob('*.py'))}|{'benchmark':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


def training(days,values,origin):
    lookup=dict(zip(days,values));start=origin
    while start in lookup:start-=timedelta(days=1)
    selected=[d for d in days if start<d<=origin]
    if len(selected)<56:raise ValueError('Fewer than 56 contiguous observed dates at cutoff')
    return selected,[lookup[d] for d in selected]


def evaluate(model,days,values,origin,targets):
    train_days,train=training(days,values,origin)
    lookup=dict(zip(days,values))
    if any(t not in lookup for t in targets):raise ValueError('Missing scored targets')
    began=time.perf_counter();model.fit(train_days,train);fit_seconds=time.perf_counter()-began
    began=time.perf_counter();predicted=model.predict(targets);latency=time.perf_counter()-began
    actual=[lookup[t] for t in targets]
    return {'origin':origin.isoformat(),'training_start':train_days[0].isoformat(),'targets':[t.isoformat() for t in targets],
            'actual':actual,'predicted':predicted,'metrics':metrics(actual,predicted,train),
            'fit_seconds':fit_seconds,'predict_seconds':latency,'warnings':getattr(model,'fit_warnings',[])}


def select_candidate(rows,h):
    scored=[]
    for row in rows:
        if len(row.get('folds',[]))!=4:continue
        folds=row['folds'][:3];actual=[];predicted=[]
        for fold in folds:
            actual+=fold['actual'][h:2*h];predicted+=fold['predicted'][h:2*h]
        if not sum(actual):continue
        wape=sum(abs(a-p) for a,p in zip(actual,predicted))/sum(actual)
        scored.append((row['model'],wape))
    if not scored:return None
    best=min(w for _,w in scored)
    # Parsimony is fixed before seeing test results.
    order=BASELINES+['croston','sba','tsb','gamma_poisson','ridge','lasso','ets','sarima','sarimax_calendar','hist_gradient']
    chosen=min((n for n,w in scored if w<=best*1.02),key=order.index)
    baseline=min(((n,w) for n,w in scored if n in BASELINES),key=lambda x:x[1])[0]
    return {'candidate':chosen,'baseline':baseline,'validation_wape':dict(scored),'horizon':h}


def run(database,output,phase):
    output.mkdir(parents=True,exist_ok=True);lock=output/'selection.json';results_file=output/(phase+'.json')
    if phase=='test':
        selection=json.loads(lock.read_text());assert selection['implementation_hash']==implementation_hash(),'Implementation changed after selection lock'
        # A marker prevents silently reopening the final test after inspecting scores.
        with (output/'TEST_OPENED').open('x') as stream:stream.write(datetime.now(timezone.utc).isoformat())
    elif lock.exists():raise ValueError('Selection already frozen; use a new run directory for development')
    db=Database('sqlite:///'+database.resolve().as_posix());context=RequestContext(session_id='benchmark',principal_id='local-benchmark',role='ADMIN')
    cutoff=date(2026,9,29) if phase=='test' else TEST_START-timedelta(days=1)
    all_series={}
    try:
        for level in LEVELS:
            all_series[level]=daily_series(db,context,cutoff,level)
    finally:db.close()
    training_hash=fingerprint({level:[{'key':list(k),'history':[(d.isoformat(),v) for d,v in zip(days,values) if d<TEST_START]} for k,(days,values) in series.items()] for level,series in all_series.items()})
    if phase=='test':assert selection['training_hash']==training_hash,'Development source changed after freeze'
    results=[];excluded=[];selections=[]
    for level,series in all_series.items():
        for key,(days,values) in series.items():
            identity=[level,*key]
            if phase=='validation':
                try:
                    for origin in ORIGINS:
                        training(days,values,origin)
                        if any(origin+timedelta(days=i) not in days for i in range(1,57)):
                            raise ValueError('Missing validation/calibration labels')
                except ValueError as error:
                    excluded.append({'series':identity,'reason':str(error)});continue
                local=[]
                for name in MODELS:
                    row={'series':identity,'model':name,'folds':[]}
                    for origin in ORIGINS:
                        try:row['folds'].append(evaluate(factory(name),days,values,origin,[origin+timedelta(days=i) for i in range(1,57)]))
                        except (ValueError,ImportError) as error:
                            row['error']=type(error).__name__+': '+str(error);break
                    local.append(row);results.append(row)
                    print(f'{level} {key} {name}: {len(row["folds"])} folds',flush=True)
                for h in HORIZONS:
                    chosen=select_candidate(local,h)
                    if chosen:selections.append({'series':identity,**chosen})
            else:
                chosen=[s for s in selection['selections'] if s['series']==identity]
                if not chosen:continue
                validation=json.loads((output/'validation.json').read_text())['results']
                candidates=[r for r in validation if r['series']==identity and len(r.get('folds',[]))==4]
                for chosen_row in chosen:
                    h=chosen_row['horizon'];origin=TEST_START-timedelta(days=h+1)
                    targets=[TEST_START+timedelta(days=block+i) for block in (0,28) for i in range(h)]
                    for candidate in candidates:
                        name=candidate['model'];row={'series':identity,'model':name,'horizon':h,'selected_before_test':name==chosen_row['candidate']}
                        try:
                            row.update(evaluate(factory(name),days,values,origin,targets))
                            _,train=training(days,values,origin)
                            row['blocks']=[{'start':row['targets'][offset], 'metrics':metrics(row['actual'][offset:offset+h],row['predicted'][offset:offset+h],train)} for offset in (0,h)]
                            calibration=candidate['folds'][3]
                            residuals=[a-p for t,a,p in zip(calibration['targets'],calibration['actual'],calibration['predicted']) if date.fromisoformat(t)<=origin]
                            for coverage in (.8,.95):
                                bands=intervals(row['predicted'],residuals,coverage)
                                row[f'interval_{coverage}']={'bands':bands,**interval_metrics(row['actual'],bands)}
                            row['calibration_warning']='Fourth validation origin, residuals restricted through final training cutoff; pooled leads and temporal dependence weaken exchangeability.'
                        except (ValueError,ImportError) as error:row['error']=str(error)
                        results.append(row)
    payload={'phase':phase,'source_label':'synthetic-workbook','seed':42,'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             'implementation_hash':implementation_hash(),'training_hash':training_hash,'results':results,'excluded':excluded,
             'test_window':'2026-08-05 to 2026-09-29 reserved; two h-day blocks starting Aug 5 and Sep 2; fixed pre-test origin and explicit h-day first-block embargo',
             'weather_ablation':'UNVERIFIED: no as-of historical forecast vintages; future observed ERA5 must not be leaked',
             'promotion':'No automatic promotion; independent significance and segment review required'}
    results_file.write_text(json.dumps(payload,indent=2,allow_nan=False),encoding='utf-8')
    if phase=='validation':
        lock.write_text(json.dumps({'implementation_hash':implementation_hash(),'training_hash':training_hash,'selections':selections,'models':MODELS,'origins':[d.isoformat() for d in ORIGINS],'horizons':HORIZONS},indent=2))
    print(f'Saved {phase}: {len(results)} model records; {len(excluded)} excluded series',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--database',type=Path,default=Path('.retailops/phase3/retailops.db'))
    parser.add_argument('--output',type=Path,default=Path('validation-output/ml/forecast-benchmark'))
    parser.add_argument('--phase',choices=['validation','test'],default='validation');args=parser.parse_args()
    if not args.database.is_file():parser.error('Source database required')
    run(args.database,args.output,args.phase)


if __name__=='__main__':main()
