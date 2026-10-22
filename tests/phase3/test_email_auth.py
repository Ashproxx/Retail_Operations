import hashlib
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.enterprise.email_auth import EmailAuth, ALLOWED
from app.security.policy import AuthenticationFailed


def test_email_tokens(monkeypatch):
    auth=EmailAuth(RuntimeSettings(_env_file=None))
    delivered=[]
    monkeypatch.setattr(auth,'send',lambda email,token:delivered.append((email,token)))
    with pytest.raises(HTTPException) as err:auth.request_token('outsider@gmail.com')
    assert err.value.status_code==403 and not delivered
    for email in ALLOWED:
        auth.request_token(email)
        assert delivered[-1][0]==email
        token=delivered[-1][1]
        assert token not in str(auth.pending)
        with pytest.raises(HTTPException):auth.verify(email,'x'*43)
        session=auth.verify(email,token)
        assert auth.authenticate(session,'test').role=='HR_ADMIN'
        with pytest.raises(HTTPException):auth.verify(email,token)
        auth.logout(session)
        with pytest.raises(AuthenticationFailed):auth.authenticate(session,'test')
        with pytest.raises(HTTPException) as err:auth.request_token(email)
        assert err.value.status_code==429
    email=next(iter(ALLOWED));auth.sent.clear();auth.request_token(email)
    digest,_,_=auth.pending[email];auth.pending[email]=(digest,0,0)
    with pytest.raises(HTTPException):auth.verify(email,delivered[-1][1])
    auth.sent.clear();auth.request_token(email)
    for _ in range(5):
        with pytest.raises(HTTPException):auth.verify(email,'z'*43)
    with pytest.raises(HTTPException):auth.verify(email,delivered[-1][1])


def test_email_sign_in_gate(tmp_path,monkeypatch):
    delivered=[]
    monkeypatch.setattr(EmailAuth,'send',lambda self,email,token:delivered.append((email,token)))
    cfg=RuntimeSettings(_env_file=None,email_login=True,database_url=SecretStr('sqlite:///'+str(tmp_path/'db')),state_dir=tmp_path/'state')
    with TestClient(create_app(cfg)) as client:
        for path in ['/','/models','/datasets','/employees','/retail']:
            assert client.get(path,follow_redirects=False).headers['location']=='/login'
        assert client.get('/login').status_code==200
        assert client.get('/api/auth/session').status_code==401
        assert client.post('/api/auth/request',json={'email':'other@gmail.com'}).status_code==403
        email='aditya.jais2005@gmail.com'
        assert client.post('/api/auth/request',json={'email':email},headers={'Origin':'https://evil.example'}).status_code==403
        assert client.post('/api/auth/request',json={'email':email.upper()}).status_code==200
        response=client.post('/api/auth/verify',json={'email':email,'token':delivered[-1][1]})
        assert response.status_code==200
        assert 'HttpOnly' in response.headers['set-cookie'] and 'SameSite=strict' in response.headers['set-cookie']
        assert client.get('/models').status_code==200
        assert client.get('/api/auth/session').json()['role']=='HR_ADMIN'
        assert client.get('/api/retail/options').status_code==403
        client.post('/api/auth/logout')
        assert client.get('/api/auth/session').status_code==401


def test_missing_sender():
    auth=EmailAuth(RuntimeSettings(_env_file=None))
    with pytest.raises(HTTPException) as err:auth.request_token('aditya.jais2005@gmail.com')
    assert err.value.status_code==503 and not auth.pending

def test_smtp_recipient_and_delivery_failure(monkeypatch):
    import smtplib
    from unittest.mock import MagicMock
    cfg=RuntimeSettings(_env_file=None,smtp_host='smtp.example.com',smtp_username='sender@example.com',smtp_sender='sender@example.com',smtp_password=SecretStr('test-password'))
    auth=EmailAuth(cfg)
    smtp=MagicMock()
    monkeypatch.setattr(smtplib,'SMTP',smtp)
    auth.request_token('omerovias@gmail.com')
    message=smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
    assert message['To']=='omerovias@gmail.com' and message['Cc'] is None and message['Bcc'] is None
    smtp.return_value.__enter__.return_value.starttls.assert_called_once()
    monkeypatch.setattr(smtplib,'SMTP',MagicMock(side_effect=smtplib.SMTPException('private details')))
    with pytest.raises(HTTPException) as err:auth.request_token('aditya.jais2005@gmail.com')
    assert err.value.status_code==503 and 'private details' not in err.value.detail
    assert 'aditya.jais2005@gmail.com' not in auth.pending
