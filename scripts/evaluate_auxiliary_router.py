import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from app.auxiliary.routing import evaluate


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reviewed',action='store_true');args=parser.parse_args()
    source=Path('docs/auxiliary/ROUTER_REVIEW.json')
    output=Path('docs/auxiliary/ROUTER_REVIEWED_RESULTS.json' if args.reviewed else 'docs/auxiliary/ROUTER_DRAFT_RESULTS.json')
    if output.exists():raise SystemExit('Refusing to overwrite existing router evidence')
    raw=source.read_bytes()
    report=evaluate(json.loads(raw)['cases'],args.reviewed)
    report.update(fixture_sha256=hashlib.sha256(raw).hexdigest(),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        status='REVIEWED_FIXTURE_DIAGNOSTIC' if args.reviewed else 'UNREVIEWED_DRAFT_DIAGNOSTIC',
        limitations=['Agent-authored paired examples; not independent natural query accuracy.',
            'No trained classifier or threshold tuning; default original router is measured.',
            'Heuristic score bins are descriptive and do not establish calibrated probabilities.',
            'Human label review and independent query collection remain acceptance requirements.'])
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(report['summaries']['all'],indent=2))


if __name__=='__main__':main()
