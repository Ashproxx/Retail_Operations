"""Data-only baseline artifacts: never deserialize executable pickle files."""
from datetime import date
import hashlib
import json
from pathlib import Path
import platform
from app.ml.models import Baseline


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def save(path: Path, model: Baseline, *, source_hash: str, features: list[str], metrics: dict, commit: str) -> None:
    if not model.days or len(source_hash)!=64 or not commit:
        raise ValueError('Fit the model and supply provenance')
    payload={'schema':1,'kind':'baseline','name':model.name,'days':[d.isoformat() for d in model.days],
             'values':model.values,'source_hash':source_hash,'features':features,'metrics':metrics,'commit':commit,
             'training_window':[model.days[0].isoformat(),model.days[-1].isoformat()],
             'versions':{'python':platform.python_version()},'promotion':'baseline_fallback'}
    path.parent.mkdir(parents=True,exist_ok=True)
    # A checksum detects corruption, not malicious replacement; use trusted local artifact storage.
    with path.open('x',encoding='utf-8') as stream:
        json.dump({'payload':payload,'sha256':fingerprint(payload)},stream,allow_nan=False,indent=2)


def load(path: Path) -> Baseline:
    if path.stat().st_size>10_000_000:
        raise ValueError('Oversized artifact')
    record=json.loads(path.read_text(encoding='utf-8')); payload=record['payload']
    if fingerprint(payload)!=record['sha256'] or payload['schema']!=1 or payload['kind']!='baseline':
        raise ValueError('Unsupported or corrupt artifact')
    return Baseline(payload['name']).fit([date.fromisoformat(d) for d in payload['days']],payload['values'])
