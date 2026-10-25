"""Read only dates through May 26, 2026; record a separate supplemental result."""
import hashlib
import importlib.metadata
import json
from datetime import date
from pathlib import Path
import sqlite3
import subprocess
from app.auxiliary.seasonal import compare


def main():
    output=Path('docs/auxiliary/SEASONAL_RESULTS.json')
    if output.exists():
        raise SystemExit('Preserve existing supplemental evidence; refusing to overwrite.')
    database=Path('.retailops/phase3/retailops.db').resolve()
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as connection:
        rows=connection.execute('SELECT day, SUM(quantity) FROM sales_transactions WHERE day <= ? GROUP BY day ORDER BY day',
                                ('2026-05-26',)).fetchall()
    result=compare([date.fromisoformat(d) for d,_ in rows],[v for _,v in rows])
    result.update(source='synthetic-workbook', seed=42,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        aggregate_source_sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
        versions={p:importlib.metadata.version(p) for p in ['numpy','scikit-learn','statsmodels']})
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result['results'],indent=2))


if __name__=='__main__':main()
