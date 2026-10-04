"""Run the local dual-model workspace against imported POC data."""
import argparse
import hashlib
from pathlib import Path
import secrets
from datetime import datetime, timezone, timedelta
import uvicorn
from pydantic import SecretStr
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.security.policy import Grant


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,default=Path('.retailops/phase3/retailops.db'))
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--role',choices=['ADMIN','HR_ADMIN','HR_USER','STORE_MANAGER','ANALYST'],default='ADMIN')
    parser.add_argument('--stores',nargs='*',default=[])
    args=parser.parse_args()
    if not args.database.is_file():parser.error('Import the sales and employee workbooks before launching; see docs/phase3/RUNBOOK.md.')
    if args.role not in ['ADMIN','HR_ADMIN'] and not args.stores:parser.error('Scoped roles require --stores with authorized store IDs.')
    token=secrets.token_urlsafe(32)
    grant=Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id='local-poc',role=args.role,
                store_ids=args.stores,expires_at=datetime.now(timezone.utc)+timedelta(hours=8))
    config=RuntimeSettings(_env_file=None,database_url=SecretStr('sqlite:///'+args.database.resolve().as_posix()),state_dir=args.database.resolve().parent/'runtime')
    app=create_app(config,runtime_factory=lambda database,settings:Runtime(database,settings,grants=[grant]))
    print(f'Local workspace: http://127.0.0.1:{args.port}/models\nAccess role: {args.role}\nTemporary token (expires in 8 hours): {token}',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=args.port)


if __name__=='__main__':main()
