"""Run the isolated real-time candidate with the existing terminal-token login."""
import argparse,hashlib,secrets
from datetime import datetime,timezone,timedelta
from pathlib import Path
import uvicorn
from pydantic import SecretStr
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.security.policy import Grant
from app.realtime.config import RealtimeSettings
from app.realtime.service import install


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--database',type=Path,default=Path('.retailops/phase3/retailops.db'));parser.add_argument('--port',type=int,default=8001);args=parser.parse_args()
    if not args.database.is_file():parser.error('Import the supplied workbooks first')
    token=secrets.token_urlsafe(32);grant=Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id='local-realtime',role='ADMIN',expires_at=datetime.now(timezone.utc)+timedelta(hours=8))
    config=RuntimeSettings(email_login=False,database_url=SecretStr('sqlite:///'+args.database.resolve().as_posix()),state_dir=args.database.resolve().parent/'realtime-runtime')
    app=create_app(config,runtime_factory=lambda db,cfg:Runtime(db,cfg,grants=[grant]));install(app,RealtimeSettings())
    print(f'Real-time candidate: http://127.0.0.1:{args.port}/models\nTemporary token (8 hours): {token}',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=args.port)


if __name__=='__main__':main()
