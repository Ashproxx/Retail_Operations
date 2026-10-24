"""Fixed development-only pooled/local/baseline comparison, no primary test access."""
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import subprocess

from app.ml.pooled import PooledBoosting
from app.ml.forecasting import ForecastModel
from app.ml.models import Baseline
from app.ml.evaluation import metrics


def evaluate(rows):
    origin = date(2026, 3, 31)
    training = [origin-timedelta(days=i) for i in range(55,-1,-1)]
    targets = [origin+timedelta(days=i) for i in range(15,29)]
    grouped = defaultdict(dict)
    for key, day, units in rows:
        if day > targets[-1]:
            raise ValueError('No later or final-test dates permitted')
        if day in grouped[key]:
            raise ValueError('Duplicate series/date')
        grouped[key][day] = units
    eligible, excluded = {}, {}
    for key, values in sorted(grouped.items()):
        if not all(d in values for d in training+targets):
            excluded[str(key)] = 'missing training or scoring dates; not zero-filled'
            continue
        eligible[key] = (training, [values[d] for d in training])
    if len(eligible) < 2:
        return {'status':'UNVERIFIED', 'reason':'Fewer than two eligible observed series', 'excluded':excluded}
    pooled = PooledBoosting().fit(eligible)
    results = []
    for key, (days, values) in eligible.items():
        actual = [grouped[key][d] for d in targets]
        models = {'pooled_hist_gradient': pooled.predict(key, targets),
                  'local_hist_gradient': ForecastModel('hist_gradient').fit(days, values).predict(targets),
                  'weekday_mean_28': Baseline('weekday_mean_28').fit(days, values).predict(targets)}
        results.append({'series':list(key), 'observations':len(actual),
            'metrics':{name:metrics(actual,pred,values) for name,pred in models.items()}})
    return {'status':'EXPLORATORY_DEVELOPMENT_COMPARISON', 'origin':str(origin),
        'training_days_per_series':56, 'embargo_days':14, 'targets':[str(d) for d in targets],
        'eligible_series':len(eligible), 'excluded':excluded, 'results':results}


def main():
    output = Path('docs/ml/POOLED_RESULTS.json')
    if output.exists():
        raise SystemExit('Preserve existing evidence; refusing to overwrite.')
    database = Path('.retailops/phase3/retailops.db').resolve()
    with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True) as connection:
        source = connection.execute('SELECT store_id, category, day, SUM(quantity) '
            'FROM sales_transactions WHERE day BETWEEN ? AND ? GROUP BY store_id, category, day '
            'ORDER BY store_id, category, day', ('2026-02-04','2026-04-28')).fetchall()
    stores = defaultdict(float)
    categories = []
    for store, category, day, units in source:
        stores[store, day] += units
        categories.append(((store,category), date.fromisoformat(day),units))
    report = {'source':'synthetic-workbook',
        'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'versions':{p:importlib.metadata.version(p) for p in ['numpy','scikit-learn']},
        'source_sha256':hashlib.sha256(json.dumps(source).encode()).hexdigest(),
        'store':evaluate([((s,),date.fromisoformat(d),v) for (s,d),v in stores.items()]),
        'store_category':evaluate(categories),
        'limitations':['One development origin; prior primary test has already been opened. No independent accuracy claim.',
            'Fixed 56-day windows and one-hot series identity; unseen series are unsupported.',
            'Coverage-based eligibility excludes sparse series; missing dates are never assumed zero.',
            'No hyperparameter search, final-test reuse, model promotion, causal interpretation or runtime integration.',
            'Point comparison only; pooled intervals and independent calibration are unverified.']}
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:{'status':report[k]['status'],'eligible':report[k].get('eligible_series',0),
                           'excluded':len(report[k]['excluded'])} for k in ['store','store_category']}))


if __name__ == '__main__':
    main()
