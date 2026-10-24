"""Frozen training-only descriptive supplement; no operational pricing action."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import subprocess

from app.auxiliary.price import price_association


def main():
    output = Path('docs/auxiliary/PRICE_RESULTS.json')
    if output.exists():
        raise SystemExit('Preserve existing evidence; refusing to overwrite.')
    database = Path('.retailops/phase3/retailops.db').resolve()
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        rows = connection.execute('SELECT day, sku_id, SUM(quantity), SUM(net_paise)/100.0 '
            'FROM sales_transactions WHERE day <= ? GROUP BY day, sku_id ORDER BY day, sku_id',
            ('2026-03-31',)).fetchall()
    result = price_association(rows)
    result.update(source='synthetic-workbook',
        code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        aggregate_source_sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
        versions={p: importlib.metadata.version(p) for p in ['numpy', 'pandas', 'statsmodels']})
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
