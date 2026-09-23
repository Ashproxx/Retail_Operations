import hashlib
from datetime import date,timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.security.policy import Grant

# Test-only credentials: never installed by the application.
TOKENS={role:('fixture-'+role+'-')*5 for role in ['admin','manager','analyst','other']}

def headers(role='admin'):
    return {'Authorization':'Bearer '+TOKENS[role]}

from app.integration.fixtures import seed

@pytest.fixture
def client(tmp_path):
    grants=[Grant(token_sha256=hashlib.sha256(TOKENS[key].encode()).hexdigest(),principal_id=key,role=role,store_ids=stores)
            for key,role,stores in [('admin','ADMIN',[]),('manager','STORE_MANAGER',['BANDRA','ANDHERI']),
                                   ('analyst','ANALYST',['BANDRA']),('other','STORE_MANAGER',['ANDHERI'])]]
    def factory(db,config):
        runtime=Runtime(db,config,grants=grants)
        seed(runtime.repository)
        return runtime
    config=RuntimeSettings(_env_file=None,database_url='sqlite+pysqlite:///'+str(tmp_path/'retail.db'),
                           state_dir=tmp_path/'state',llm_provider='deterministic')
    with TestClient(create_app(config,factory)) as c:yield c
