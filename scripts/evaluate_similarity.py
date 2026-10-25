"""Read-only training aggregates and unlabeled product-pair review queue."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import subprocess
from app.auxiliary.similarity import compare_rankings


def main():
    output = Path('docs/auxiliary/SIMILARITY_RESULTS.json')
    if output.exists():
        raise SystemExit('Preserve existing evidence; refusing to overwrite.')
    database = Path('.retailops/phase3/retailops.db').resolve()
    with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True) as connection:
        rows = connection.execute('SELECT sku_id, SUM(quantity), SUM(net_paise)/100.0, '
            'COUNT(DISTINCT day), COUNT(DISTINCT store_id) FROM sales_transactions '
            'WHERE day <= ? GROUP BY sku_id ORDER BY sku_id', ('2026-03-31',)).fetchall()
    result = compare_rankings(rows)
    result.update(source='synthetic-workbook', training_end='2026-03-31',
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        aggregate_source_sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
        versions={p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'scikit-learn']},
        limitations=['Method agreement is not semantic relevance, substitution or competitive accuracy.',
            'Observed exposure and realized price confound these descriptive rankings.',
            'Standardization is fit on training products only; missing days are not zero-filled.',
            'Ties break by SKU; arbitrary tie order can affect Spearman agreement.',
            'The union of two top-five lists is a biased review pool, not an independent retrieval test.',
            'No human labels, runtime integration, promotion or external data transmission.'])
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'review_queue'}, indent=2))


if __name__ == '__main__':
    main()
