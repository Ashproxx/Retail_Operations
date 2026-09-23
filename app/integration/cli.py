"""Local operator commands. Import is privileged filesystem access, not a public API."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
from app.api.schemas import Role
from app.integration.config import RuntimeSettings
from app.integration.loader import TabularLoader
from app.integration.registry import REGISTRY, contracts
from app.integration.repository import Repository
from app.services.database_service import Database

def private_write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:stream.write(text)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    init=commands.add_parser('init');init.add_argument('--principal',default='local-admin')
    load=commands.add_parser('load');load.add_argument('--agent',required=True,choices=REGISTRY)
    load.add_argument('--file',required=True,type=Path);load.add_argument('--mapping',required=True,type=Path)
    load.add_argument('--stores',type=Path);load.add_argument('--fixture',action='store_true')
    schema=commands.add_parser('schema');schema.add_argument('--agent',required=True,choices=REGISTRY)
    model=commands.add_parser('fixture-model');model.add_argument('--output',type=Path,default=Path('models/fixture-bow'))
    args=parser.parse_args()
    if args.command=='init':
        if Path('.env').exists() or Path('secrets/grants.json').exists():parser.error('Configuration exists; preserve it and provision additional grants manually.')
        token=secrets.token_urlsafe(32)
        private_write(Path('secrets/admin-token.txt'),token+'\n')
        private_write(Path('secrets/grants.json'),json.dumps([{'token_sha256':hashlib.sha256(token.encode()).hexdigest(),
            'principal_id':args.principal,'role':'ADMIN','store_ids':[]}],indent=2)+'\n')
        private_write(Path('.env'),'RETAILOPS_DATABASE_URL=sqlite+pysqlite:///./retailops.db\nRETAILOPS_STATE_DIR=.retailops\nRETAILOPS_GRANTS_FILE=secrets/grants.json\nRETAILOPS_INTEGRITY_KEY='+secrets.token_urlsafe(32)+'\nRETAILOPS_LLM_PROVIDER=ollama\nRETAILOPS_OLLAMA_MODEL=\n')
        print('Local credentials created in secrets/ and .env. Nothing was printed or uploaded.')
    elif args.command=='schema':
        record,query,_=contracts(args.agent)
        print(json.dumps({'record':record.model_json_schema(),'query':query.model_json_schema()},indent=2))
    elif args.command=='fixture-model':
        if args.output.exists():parser.error('Output already exists')
        from sentence_transformers import SentenceTransformer
        from sentence_transformers.sentence_transformer import modules as models
        SentenceTransformer(modules=[models.BoW(['inventory','stock','reorder','refund','receipt','returns','days',
            'shipping','warehouse','policy','thirty','seven','customer','service','faq','opening','hours','nine','five']),
            models.Normalize()]).save(str(args.output))
        print('Synthetic lexical test model created; this is not a pretrained semantic model.')
    else:
        config=RuntimeSettings();db=Database(config.database_url.get_secret_value())
        try:
            report=TabularLoader(Repository(db),args.agent,fixture=args.fixture,
                store_names=json.loads(args.stores.read_text()) if args.stores else None).load(args.file,json.loads(args.mapping.read_text()))
            print(report.model_dump_json(indent=2))
        finally:db.close()

if __name__=='__main__':main()
