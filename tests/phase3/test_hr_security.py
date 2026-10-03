import hashlib
import pytest
from sqlalchemy import select
from app.api.schemas import RequestContext
from app.security.policy import AccessDenied,Grant,TokenAuthenticator,authorize
from app.employees.security import profile,scope,audit,SENSITIVE
from app.employees.data import Employee
from app.security.audit import AuditChain,verify_chain
from types import SimpleNamespace


def context(role,stores=['S1']):return RequestContext(principal_id='test-user',session_id='hr',role=role,store_ids=stores)


def test_server_role_scope_and_redaction(tmp_path):
    record=dict(employee_id='E1',store_id='S1',full_name='Test Person',monthly_gross_salary_inr=23456,date_of_birth='1990-01-01',performance_rating=None)
    assert not SENSITIVE.intersection(profile(record,context('STORE_MANAGER')))
    assert profile(record,context('HR_USER'))['monthly_gross_salary_inr']==23456
    assert profile(record,context('HR_ADMIN',[]))['performance_rating'] is None
    for ctx in [context('ANALYST'),context('SUPPORT_AGENT'),context('HR_USER',['S2'])]:
        with pytest.raises(AccessDenied):profile(record,ctx)
    with pytest.raises(AccessDenied):scope(select(Employee),Employee,context('ANALYST'),detail=True)
    with pytest.raises(AccessDenied):authorize(context('HR_USER'),'analytics.read','S1')
    token='synthetic-test-token-at-least-32-chars'
    auth=TokenAuthenticator([Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id='hr',role='HR_USER',store_ids=['S1'])])
    assert auth.authenticate(token,'s').role.value=='HR_USER'
    runtime=SimpleNamespace(audit=AuditChain(tmp_path/'audit.jsonl'))
    audit(runtime,context('HR_USER'),'employee.profile','success',['E1'],profile(record,context('HR_USER')).keys())
    rows=runtime.audit.read();assert verify_chain(rows)['count']==1
    assert 'monthly_gross_salary_inr' in rows[0]['event']['fields_accessed']
    assert '23456' not in (tmp_path/'audit.jsonl').read_text()
