"""Offline API demo in a temporary database; never touches operational state."""
import hashlib
import json
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.integration.fixtures import seed
from app.security.policy import Grant

def main():
    with TemporaryDirectory() as directory:
        token=secrets.token_urlsafe(32)
        grant=Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id='fixture-user',role='STORE_MANAGER',store_ids=['BANDRA','ANDHERI'])
        def factory(db,config):
            runtime=Runtime(db,config,grants=[grant]);seed(runtime.repository);return runtime
        config=RuntimeSettings(_env_file=None,database_url='sqlite+pysqlite:///'+str(Path(directory)/'demo.db'),
            state_dir=Path(directory)/'state',llm_provider='deterministic')
        with TestClient(create_app(config,factory)) as client:
            for message,parameters in [
                ('Which products are low in Bandra?',{}),('What about Andheri?',{}),
                ('Inventory is low but demand is increasing. What actions should be considered?',
                 {'store_id':'BANDRA','sku_id':'SHIRT-1','as_of':'2026-09-22'}),
                ('Show total units sold by store.',{}),('Unknown request',{})]:
                result=client.post('/api/chat',headers={'Authorization':'Bearer '+token},json={
                    'message':message,'session_id':'fixture-demo','parameters':parameters})
                result.raise_for_status();body=result.json()
                print(json.dumps({'query':message,'status':body['data']['status'],'agents':body['agents_used'],
                                  'answer':body['answer'],'fixture':body['data']['fixture']}))

if __name__=='__main__':main()
