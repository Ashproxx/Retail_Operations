from types import SimpleNamespace
from uuid import uuid4
from app.api.schemas import RequestContext
from app.integration.repository import Repository
from app.security.audit import AuditChain
from app.services.database_service import Database
from app.enterprise import imports
from app.enterprise.retail import RetailService
from app.enterprise.contracts import WorkspaceTurn
from tests.phase3.test_imports import small_sales


def test_sql_conversation_latest_chart_and_inventory_boundary(tmp_path,monkeypatch):
    path=tmp_path/'sales.xlsx';path.write_bytes(b'fixture')
    monkeypatch.setattr(imports,'sheets',lambda *a:small_sales())
    db=Database('sqlite:///'+str(tmp_path/'db'));imports.import_sales(db,path)
    rt=SimpleNamespace(repository=Repository(db),audit=AuditChain(tmp_path/'audit'))
    svc=RetailService(rt)
    def ask(message='',**kw):
        ctx=RequestContext(principal_id='m',session_id='test',role='STORE_MANAGER',store_ids=['S1'])
        return svc.run(WorkspaceTurn(session_id='test',message=message,**kw),ctx)
    assert ask('How were sales?')['choices'][0]['label']=='Test City'
    assert ask(action='select',value='S1')['status']=='needs_clarification'
    result=ask(action='select',value='latest')
    assert result['metrics']['Net sales (INR)']=='1199'
    result=ask('Show 2030-01-01 sales')
    assert result['status']=='no_data' and '2026-09-29' in result['summary']
    result=ask(action='latest');assert result['metrics']['Orders']==1
    assert ask('Show pie chart')['visualization']['datasets'][0]['values']==[1199.0]
    assert ask('current stock')['status']=='unavailable'
    assert ask('What is an employee salary?')['workspace']=='/employees'
    result=ask('competitor estimates');assert result['table'][0]['estimated_units']==5
    assert result['metrics']['Our units in benchmark weeks']==1
    db.close()
