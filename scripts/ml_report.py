"""Generate an honest scorecard from a recorded baseline experiment."""
import argparse
import json
from pathlib import Path


def report(source: Path, output: Path) -> None:
    record=json.loads(source.read_text(encoding='utf-8'))
    lines=['# AIML scorecard','','Generated from '+str(source)+'.',
           f"Source: {record['source_label']}; code: {record['code_commit']}; run: {record['date']}.",
           '', 'No independent test accuracy is verified by a validation-only run.', '',
           '| Pillar | Dataset | Test metric | Status |','|---|---|---|---|']
    for name in ['Forecasting','Intent routing','RAG retrieval','Anomaly detection','Product similarity','Forecast-driven decisions']:
        lines.append(f'| {name} | {record["source_label"] if name=="Forecasting" else "Not evaluated"} | Not evaluated | UNVERIFIED |')
    lines+=['','## Baseline parity diagnostics (not test accuracy)','','| Series | Model | One-step MAE | WAPE |','|---|---|---:|---:|']
    for row in record['results']:
        if 'parity' in row:
            p=row['parity'];lines.append(f"| {' / '.join(row['series'])} | {row['model']} | {p['mae']:.6f} | {p['wape']} |")
    lines+=['','Forecast baselines reproduce the existing algorithm; this does not certify new ML performance. No automatic model promotion.']
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=Path('validation-output/ml/baseline.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/ml/AIML_SCORECARD.md'));args=parser.parse_args();report(args.input,args.output)


if __name__=='__main__':main()
