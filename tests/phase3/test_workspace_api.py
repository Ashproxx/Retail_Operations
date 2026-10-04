import hashlib
from fastapi.testclient import TestClient
from pydantic import SecretStr
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.security.policy import Grant
from app.enterprise import imports
from app.employees import data
from app.services.database_service import Database
from tests.phase3.test_imports import small_sales
from tests.phase3.test_employee_data import small_employees


def test_authenticated_workspaces_and_cross_model_memory(tmp_path,monkeypatch):
    url='sqlite:///'+str(tmp_path/'db');db=Database(url)
    sales=tmp_path/'sales.xlsx';sales.write_bytes(b'sales')
    employees=tmp_path/'employees.xlsx';employees.write_bytes(b'employees')
    monkeypatch.setattr(imports,'sheets',lambda *a:small_sales());imports.import_sales(db,sales)
    monkeypatch.setattr(data,'sheets',lambda *a:small_employees());data.import_employees(db,employees);db.close()
    tokens={role:(role+'x'*40) for role in ['ADMIN','HR_ADMIN','STORE_MANAGER','ANALYST']}
    grants=[Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id=role,role=role,store_ids=['S1']) for role,token in tokens.items()]
    app=create_app(RuntimeSettings(_env_file=None,database_url=SecretStr(url),state_dir=tmp_path/'state'),runtime_factory=lambda db,cfg:Runtime(db,cfg,grants=grants))
    with TestClient(app) as client:
        def headers(role='ADMIN'):return {'Authorization':'Bearer '+tokens[role]}
        def turn(model,message='',role='ADMIN',**extra):return client.post('/api/'+model+'/chat',headers=headers(role),json={'session_id':'shared-id','message':message,**extra})
        for path in ['/','/models','/retail','/employees','/employee-work','/management']:
            response=client.get(path,headers={'Accept':'text/html'});assert response.status_code==200
            assert 'script-src \'self\'' in response.headers['content-security-policy']
        for path in ['/api/retail/options','/api/employees/options','/api/employees/search?q=Test','/api/employees/overview']:
            assert client.get(path).status_code==401
        assert turn('retail','Show latest sales in Test City').json()['metrics']['Net sales (INR)']=='1199'
        assert turn('employees','Tell me about Test Person').json()['profile']['Profile']['full_name']=='Test Person'
        assert turn('retail','Show pie chart').json()['visualization']['type']=='pie'
        assert '20,000' in turn('employees','What is her salary?').json()['summary']
        assert turn('retail','sales',role='HR_ADMIN').status_code==403
        assert client.get('/api/employees/search?q=Test',headers=headers('ANALYST')).status_code==403
        profile=turn('employees','Tell me about Test Person',role='STORE_MANAGER').json()['profile']
        assert 'Compensation' not in profile and 'Benefits' not in profile
        assert turn('employees','What is her salary?',role='STORE_MANAGER').json()['status']=='denied'
        assert turn('employees','Show Test Person',role='ANALYST').json()['status']=='denied'
        assert turn('employees','x',role='ADMIN',store_ids=['S2']).status_code==422
        assert turn('employees',action='select',value='unknown').status_code==403


def test_fresh_app_creates_phase3_tables(tmp_path):
    app=create_app(RuntimeSettings(_env_file=None,database_url=SecretStr('sqlite:///'+str(tmp_path/'fresh')),state_dir=tmp_path/'state'))
    with TestClient(app):
        from sqlalchemy import inspect
        assert {'retail_products','sales_transactions','employees','store_staffing'} <= set(inspect(app.state.database.engine).get_table_names())
