"""Read-only local benchmark; writes aggregate metrics without source records."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import subprocess
from app.auxiliary.evaluation import delivery_evaluation, product_segments, anomaly_evaluation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=Path('.retailops/phase3/retailops.db'))
    parser.add_argument('--output', type=Path, default=Path('docs/auxiliary/RESULTS.json'))
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Results already exist. Preserve the frozen run; do not silently overwrite it.')
    with sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro', uri=True) as connection:
        payloads = [r[0] for r in connection.execute('select payload from sales_transactions order by txn_id')]
    rows = [json.loads(r) for r in payloads]
    report = {'source': 'synthetic-workbook', 'seed': 42,
        'source_sha256': hashlib.sha256('\n'.join(payloads).encode()).hexdigest(),
        'code_commit': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'python': platform.python_version(),
        'versions': {p: importlib.metadata.version(p) for p in ['scikit-learn','numpy','scipy']},
        'delivery': delivery_evaluation(rows), 'segmentation': product_segments(rows),
        'anomalies': anomaly_evaluation(rows),
        'routing': {'status': 'UNVERIFIED', 'reason': '200+ human-reviewed queries are not supplied.'},
        'retrieval': {'status': 'UNVERIFIED', 'reason': 'Expanded 50-positive/15-negative benchmark not evaluated.'},
        'elasticity': {'status': 'UNVERIFIED', 'reason': 'Observed transaction prices have selection/exposure confounding; no causal effect is established.'},
        'reorder_risk': {'status': 'UNVERIFIED', 'reason': 'No stock or lead-time ground truth.'}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({k: v.get('status') for k,v in report.items() if isinstance(v,dict) and 'status' in v}))


if __name__ == '__main__':
    main()
