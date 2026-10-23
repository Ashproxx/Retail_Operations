"""Candidate-only launch; reuses existing authentication and runtime."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import secrets
from pydantic import SecretStr
import uvicorn
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.security.policy import Grant
from app.ml_dashboard.routes import install


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,default=Path('.retailops/phase3/retailops.db'))
    parser.add_argument('--port',type=int,default=8002)
    parser.add_argument('--role',choices=['ADMIN','ANALYST','STORE_MANAGER'],default='ADMIN')
    parser.add_argument('--stores',nargs='*',default=[])
    args=parser.parse_args()
    if not args.database.is_file(): parser.error('Import the source workbooks first.')
    if args.role!='ADMIN' and not args.stores: parser.error('Scoped roles require --stores.')
    token=secrets.token_urlsafe(32)
    grant=Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id='local-ml-review',
        role=args.role,store_ids=args.stores,expires_at=datetime.now(timezone.utc)+timedelta(hours=8))
    settings=RuntimeSettings(email_login=False,database_url=SecretStr('sqlite:///'+args.database.resolve().as_posix()),
        state_dir=args.database.resolve().parent/'ml-review-runtime')
    api=create_app(settings,runtime_factory=lambda db,config:Runtime(db,config,grants=[grant]))
    install(api)
    print(f'Model review: http://127.0.0.1:{args.port}/ml\nTemporary token (8 hours): {token}',flush=True)
    uvicorn.run(api,host='127.0.0.1',port=args.port)


if __name__=='__main__':main()
