"""Render the same measured forecasting results for documentation and the ML UI."""
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path
from statistics import mean
from app.ml.evaluation import paired_bootstrap


def generate(folder:Path,output:Path):
    validation=json.loads((folder/'validation.json').read_text());test=json.loads((folder/'test.json').read_text())
    selection=json.loads((folder/'selection.json').read_text())
    groups=defaultdict(list)
    for row in test['results']:
        if 'metrics' in row:groups[(row['series'][0],row['model'],row['horizon'])].append(row)
    leaderboard=[]
    for (level,model,h),rows in sorted(groups.items()):
        item={'level':level,'model':model,'horizon':h,'series_count':len(rows),'observations':sum(r['metrics']['n'] for r in rows)}
        for metric in ['mae','rmse','wape','mase','bias']:
            values=[r['metrics'][metric] for r in rows if r['metrics'][metric] is not None]
            item[metric]=mean(values) if values else None
        for coverage in (.8,.95):
            values=[r[f'interval_{coverage}']['coverage'] for r in rows if f'interval_{coverage}' in r]
            item[f'coverage_{coverage}']=mean(values) if values else None
        item['fit_seconds']=mean(r['fit_seconds'] for r in rows);item['predict_seconds']=mean(r['predict_seconds'] for r in rows)
        leaderboard.append(item)
    decisions=[]
    for selected in selection['selections']:
        h=selected['horizon'];identity=selected['series'];name=selected['candidate'];baseline=selected['baseline']
        candidates={r['model']:r for r in validation['results'] if r['series']==identity and len(r.get('folds',[]))==4}
        tested={r['model']:r for r in test['results'] if r['series']==identity and r['horizon']==h and 'metrics' in r}
        if name not in tested or baseline not in tested:
            decisions.append({**selected,'gate':'UNVERIFIED','reason':'Missing paired final-test coverage'});continue
        def errors(model):
            return [p-a for f in candidates[model]['folds'][:3] for a,p in zip(f['actual'][h:2*h],f['predicted'][h:2*h])]
        comparison=paired_bootstrap(errors(name),errors(baseline))
        score=tested[name]['metrics'];base=tested[baseline]['metrics']
        qualifies=name!=baseline and comparison.get('candidate_better',False) and score['mase'] is not None and score['mase']<1 and score['wape']<=base['wape']
        decisions.append({**selected,'validation_comparison':comparison,'test_wape':score['wape'],'baseline_test_wape':base['wape'],
                          'gate':'ELIGIBLE_FOR_REVIEW' if qualifies else 'RETAIN_BASELINE','promoted':False})
    summary={'source_label':'synthetic-workbook','code_commit':test['code_commit'],'implementation_hash':test['implementation_hash'],
             'leaderboard':leaderboard,'decisions':decisions,'excluded_by_level':dict(Counter(r['series'][0] for r in validation['excluded'])),
             'validation_failures':[{'series':r['series'],'model':r['model'],'error':r['error']} for r in validation['results'] if 'error' in r],
             'test_failures':[{'series':r['series'],'model':r['model'],'horizon':r['horizon'],'error':r['error']} for r in test['results'] if 'error' in r],
             'curves':[r for r in test['results'] if r.get('selected_before_test') and 'metrics' in r],
             'limitations':['Synthetic results are not real-world accuracy.','No causal price/weather claim.','Weather ablation unavailable without historical forecast vintages.',
                'Only complete eligible series were scored; no missing days were turned into zero sales.',
                'Conformal calibration pools leads and temporal dependence weakens exchangeability. Empirical coverage is reported.',
                'One predefined setting per model, no broad hyperparameter search. Global pooled boosting and feature importance comparisons remain incomplete.',
                'Block bootstrap concatenates three separated validation windows; significance is exploratory, not a deployment guarantee.',
                'Quantile boosting is implemented and unit tested but not included in this final comparison. Pinball comparison remains unverified.',
                'Store/category and store/SKU tables report exclusions rather than invented scores.']}
    output.mkdir(parents=True,exist_ok=True);(output/'FORECAST_RESULTS.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    lines=['# Measured forecasting comparison','','Source: **synthetic-workbook**. Independent frozen test run at code `'+test['code_commit']+'`.',
           '', 'Dates reserved: 2026-08-05–2026-09-29. Two h-day blocks begin August 5 and September 2; both use the same pre-test fit. First-block lead is h+1 to 2h, second-block lead h+29 to 2h+28. Model selection used only the first three validation origins. Calibration residuals end no later than the final training cutoff.',
           '', 'Reported values are unweighted averages across eligible series, with each series metric calculated on both scored blocks. They are not volume-weighted chain totals. No model was automatically promoted.',
           '', '| Level | Model | h | Series | MAE | RMSE | WAPE | MASE | Bias | 80% coverage | 95% coverage | Fit s | Predict s |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    def fmt(value):return 'N/A' if value is None else f'{value:.4f}'
    for r in leaderboard:
        lines.append('| '+' | '.join([r['level'],r['model'],str(r['horizon']),str(r['series_count'])]+[fmt(r[k]) for k in ['mae','rmse','wape','mase','bias','coverage_0.8','coverage_0.95','fit_seconds','predict_seconds']])+' |')
    lines+=['','## Coverage and failures','',json.dumps(summary['excluded_by_level']),
            f"Validation optimizer/availability failures: {len(summary['validation_failures'])}; final-test failures: {len(summary['test_failures'])}.",
            '', '## Frozen selection review','', '| Series | h | Selected before test | Baseline | Decision |','|---|---:|---|---|---|']
    for r in decisions:lines.append(f"| {' / '.join(r['series'])} | {r['horizon']} | {r['candidate']} | {r['baseline']} | {r['gate']} |")
    lines+=['','## Limitations','']+['- '+x for x in summary['limitations']]
    lines+=['','## Reproduction','','Run validation and test once in a fresh output directory using `python -m scripts.benchmark_forecasting --phase validation` then `--phase test`. The TEST_OPENED marker prevents accidental retuning on the same test. Generate this document with `python -m scripts.forecast_report --input <run-directory>`. Changing models after reading the test requires a new untouched evaluation dataset, not deletion of the marker.']
    (output/'MODEL_COMPARISON.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=Path('validation-output/ml/forecast-benchmark-final'));parser.add_argument('--output',type=Path,default=Path('docs/ml'));args=parser.parse_args();generate(args.input,args.output)
