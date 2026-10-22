"""Single-process, email-verified HR sessions for the local testing server."""
import hashlib
import hmac
import secrets
import smtplib
import ssl
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from threading import Lock
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.security.policy import AuthenticationFailed, Grant, TokenAuthenticator
from pathlib import Path

ALLOWED = frozenset({'aditya.jais2005@gmail.com', 'omerovias@gmail.com', 'ashwinkm.2005@gmail.com'})
COOKIE = 'retailops_session'
router = APIRouter()

class EmailInput(BaseModel):
    email: str = Field(max_length=254)

class VerifyInput(EmailInput):
    token: str = Field(min_length=32, max_length=128)

class EmailAuth:
    # shortcut: sessions are process-local; use shared storage before running multiple workers.
    def __init__(self, config):
        self.config = config
        self.pending = {}
        self.sessions = {}
        self.sent = {}
        self.lock = Lock()

    def send(self, email, token):
        c = self.config
        if not all([c.smtp_host, c.smtp_username, c.smtp_password, c.smtp_sender]):
            raise HTTPException(503, 'Email delivery is not configured. Ask the project owner to configure the sender.')
        msg = EmailMessage()
        msg['From'], msg['To'], msg['Subject'] = c.smtp_sender, email, 'RetailOps AI access token'
        msg.set_content(f'Your RetailOps AI access token is:\n\n{token}\n\nEnter this on the sign-in page within 10 minutes. It can be used once. Do not share it. If you did not request this, ignore this email.')
        try:
            with smtplib.SMTP(c.smtp_host, c.smtp_port, timeout=15) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(c.smtp_username, c.smtp_password.get_secret_value())
                smtp.send_message(msg)
        except (OSError, smtplib.SMTPException):
            raise HTTPException(503, 'Email could not be sent. Ask the project owner to check the sender settings.') from None

    def request_token(self, email):
        if email not in ALLOWED:
            raise HTTPException(403, "You don't have access to this page.")
        with self.lock:
            now = time.time()
            if now - self.sent.get(email, 0) < 60:
                raise HTTPException(429, 'Please wait one minute before requesting another token.')
            self.sent[email] = now
            token = secrets.token_urlsafe(32)
            self.send(email, token)
            self.pending[email] = (hashlib.sha256(token.encode()).hexdigest(), now + 600, 0)

    def verify(self, email, token):
        with self.lock:
            record = self.pending.get(email)
            if not record or record[1] <= time.time() or record[2] >= 5:
                raise HTTPException(401, 'Invalid or expired token. Request a new token.')
            digest, expires, attempts = record
            self.pending[email] = (digest, expires, attempts + 1)
            if not hmac.compare_digest(digest, hashlib.sha256(token.encode()).hexdigest()):
                raise HTTPException(401, 'Invalid or expired token. Request a new token.')
            del self.pending[email]
            session = secrets.token_urlsafe(32)
            now = datetime.now(timezone.utc)
            self.sessions = {k:g for k,g in self.sessions.items() if g.expires_at > now and g.principal_id != email}
            digest = hashlib.sha256(session.encode()).hexdigest()
            self.sessions[digest] = Grant(token_sha256=digest, principal_id=email, role='HR_ADMIN', expires_at=now + timedelta(hours=8))
            return session

    def authenticate(self, token, session_id):
        with self.lock:
            return TokenAuthenticator(list(self.sessions.values())).authenticate(token, session_id)

    def logout(self, token):
        with self.lock:
            self.sessions.pop(hashlib.sha256(token.encode()).hexdigest(), None)


def state(request):
    auth = request.app.state.email_auth
    if auth is None:
        raise HTTPException(404)
    if request.method == 'POST':
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            raise HTTPException(403, 'Invalid origin.')
    return auth

@router.get('/login')
def login():
    return FileResponse(Path(__file__).parent/'static'/'login.html', headers={'Cache-Control':'no-store', 'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})

@router.get('/api/auth/session')
def session(request: Request):
    auth = request.app.state.email_auth
    if auth is None:
        return {'enabled':False}
    ctx = auth.authenticate(request.cookies.get(COOKIE,''), 'email-session')
    return {'enabled':True, 'email':ctx.principal_id, 'role':ctx.role}

@router.post('/api/auth/request')
def request_token(body: EmailInput, request: Request):
    state(request).request_token(body.email.strip().lower())
    return {'message':'Access token sent. Check your inbox and spam folder.'}

@router.post('/api/auth/verify')
def verify(body: VerifyInput, request: Request, response: Response):
    token = state(request).verify(body.email.strip().lower(), body.token.strip())
    response.set_cookie(COOKIE, token, httponly=True, secure=request.url.scheme=='https', samesite='strict', max_age=28800)
    response.headers['Cache-Control'] = 'no-store'
    return {'ok':True}

@router.post('/api/auth/logout')
def logout(request: Request, response: Response):
    state(request).logout(request.cookies.get(COOKIE,''))
    response.delete_cookie(COOKIE)
    return {'ok':True}
