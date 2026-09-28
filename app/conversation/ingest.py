"""Explicit local operator import: python -m app.conversation.ingest --help."""
import argparse
import csv
import json
from pathlib import Path
from app.conversation.catalog import Observation, import_observations
from app.integration.config import RuntimeSettings
from app.services.database_service import Database


def load(path, mapping):
    if path.stat().st_size > 20_000_000: raise ValueError('File limit is 20 MB')
    if path.suffix.lower() == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.reader(f))
    elif path.suffix.lower() == '.xlsx':
        from openpyxl import load_workbook
        book = load_workbook(path, read_only=True, data_only=False)
        try: rows = list(book.active.values)
        finally: book.close()
    else: raise ValueError('Use CSV or XLSX')
    if not rows or len(rows)>10001: raise ValueError('Supply a header and at most 10000 observations')
    headers = [str(x or '').strip() for x in rows[0]]
    if len(headers)>100 or len(headers)!=len(set(headers)): raise ValueError('Duplicate or too many headers')
    if not set(mapping)<=set(Observation.model_fields): raise ValueError('Unknown target column')
    if not set(mapping.values())<=set(headers): raise ValueError('Mapped source column is absent')
    result = []
    for values in rows[1:]:
        if not any(v is not None and v!='' for v in values): continue
        if len(values)!=len(headers): raise ValueError('Ragged row')
        if any(isinstance(v,str) and v.startswith('=') for v in values): raise ValueError('Formula cells are unsupported')
        original = dict(zip(headers,values))
        mapped = {target:original[source] for target,source in mapping.items()}
        for field,value in list(mapped.items()):
            if hasattr(value,'date') and field=='date':mapped[field]=value.date().isoformat()
            elif value=='':mapped[field]=None
        clean = Observation.model_validate(mapped).model_dump(mode='json')
        result.append((clean,original))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--file',required=True,type=Path);p.add_argument('--mapping',required=True,type=Path)
    p.add_argument('--fixture',action='store_true');args=p.parse_args()
    records=load(args.file,json.loads(args.mapping.read_text()))
    # Original source columns are retained alongside validated canonical data.
    db=Database(RuntimeSettings().database_url.get_secret_value())
    try:
        report=import_observations(db,[r[0] for r in records],source=args.file.name,fixture=args.fixture,raw_sources=[r[1] for r in records])
        print(json.dumps(report))
    finally:db.close()

if __name__=='__main__':main()
