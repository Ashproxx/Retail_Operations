"""Actual local inference smoke test. Only synthetic text is sent to the model."""
import argparse
import asyncio
import json
from pathlib import Path
import httpx
from app.integration.llm import OllamaProvider

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:11434')
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    spec=json.loads(Path('evaluation/models.json').read_text())['ollama']
    with httpx.Client(timeout=20,trust_env=False) as client:
        version=client.get(args.url+'/api/version');version.raise_for_status()
        tags=client.get(args.url+'/api/tags');tags.raise_for_status()
    info=next(m for m in tags.json()['models'] if m['name']==spec['model'])
    draft=asyncio.run(OllamaProvider(args.url,spec['model'],timeout=120).draft(
        'Synthetic fixture only: Bandra has two available units of SHIRT-1. No replenishment order was placed.'))
    report={'fixture':True,'provider':'ollama','server_version':version.json()['version'],'model':spec['model'],
        'model_digest':info['digest'],'nonempty_response':bool(draft.strip()),'response_characters':len(draft),
        'claim':'Actual local-model transport/inference works. Generated answer factuality is not certified.'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
