"""One fixed supplemental development run, without reading final-test labels."""
from datetime import date
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import subprocess
from app.ml.supplement import evaluate


def main():
    output=Path('docs/ml/QUANTILE_IMPORTANCE_RESULTS.json')
    if output.exists():raise SystemExit('Refusing to replace existing supplemental evidence')
    path=Path('.retailops/phase3/retailops.db').resolve()
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        rows=db.execute('SELECT day,SUM(quantity) FROM sales_transactions WHERE day<=? GROUP BY day ORDER BY day',('2026-04-28',)).fetchall()
    result=evaluate([date.fromisoformat(d) for d,_ in rows],[v for _,v in rows])
    result.update(source='synthetic-workbook',seed=42,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
        versions={p:importlib.metadata.version(p) for p in ['scikit-learn','numpy']})
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['quantile_raw_pinball','quantile_crossing_dates','quantile_ordered_80','baseline_conformal_80']},indent=2))


if __name__=='__main__':main()
