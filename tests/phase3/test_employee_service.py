from types import SimpleNamespace
from copy import deepcopy
import pytest
from sqlalchemy import insert
from app.api.schemas import RequestContext
from app.services.database_service import Database
from app.integration.repository import Repository
from app.security.audit import AuditChain
from app.employees.data import Employee,import_employees
from app.employees import data
from app.employees.service import EmployeeService
from app.enterprise.contracts import WorkspaceTurn
from tests.phase3.test_employee_data import small_employees


def test_name_followups_ambiguity_missing_rating_and_scope(tmp_path,monkeypatch):
    db=Database('sqlite:///'+str(tmp_path/'db'));path=tmp_path/'input.xlsx';path.write_bytes(b'test');records=small_employees()
    records['Employee_Master'][0]['full_name']='Anjali Example'
    second={**records['Employee_Master'][0],'employee_id':'E2','full_name':'Anjali Other'}
    records['Employee_Master'].append(second);records['Store_Staffing'][0].update(headcount=2,active_headcount=2)
    monkeypatch.setattr(data,'sheets',lambda *a:records);import_employees(db,path)
    rt=SimpleNamespace(repository=Repository(db),audit=AuditChain(tmp_path/'audit'));svc=EmployeeService(rt)
    def ask(message='',role='HR_USER',stores=['S1'],**kw):
        ctx=RequestContext(principal_id=role,role=role,session_id='same',store_ids=stores)
        return svc.run(WorkspaceTurn(session_id='same',message=message,**kw),ctx)
    assert len(ask('Show Anjali')['choices'])==2
    result=ask(action='select',value='E1');assert result['profile']['Profile']['full_name']=='Anjali Example'
    assert '95%' in ask('What is her attendance?')['summary']
    assert '20,000' in ask('What about her salary?')['summary']
    assert 'No performance rating' in ask('What is her performance rating?')['summary']
    assert ask('Who should be fired?')['status']=='human_review'
    assert ask('How much sales did she generate?')['status']=='unavailable'
    assert ask('Tell me about Anjali CompletelyUnknown')['status']=='needs_clarification'
    assert 'profile' not in ask('Tell me about Nonexistent Person')
    assert ask('Show Anjali salary',role='ANALYST')['status']=='denied'
    assert 'Compensation' not in ask('Tell me about Anjali Example',role='STORE_MANAGER')['profile']
    assert ask('What is her attendance?',role='HR_USER',stores=['S2'])['status']=='needs_clarification'
    assert '20000' not in (tmp_path/'audit').read_text()
    db.close()
