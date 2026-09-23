"""Synthetic local security workflow; generates ephemeral keys in memory."""
import hashlib,secrets,json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from app.api.schemas import Role,AuditEvent
from app.security.policy import Grant,TokenAuthenticator
from app.security.integrity import Document,seal
from app.security.retrieval import retrieve_verified
from app.security.audit import AuditChain,verify_chain

def main():
    token=secrets.token_urlsafe(32);key=secrets.token_bytes(32)
    auth=TokenAuthenticator([Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id='fixture-user',role=Role.SUPPORT_AGENT,store_ids=['fixture-store'])])
    context=auth.authenticate(token,'fixture-session')
    document=Document(document_id='fixture-policy',version='1',store_id='fixture-store',domain='support',source='fixture://policy',text='Synthetic policy excerpt; not a real retailer policy.')
    results=retrieve_verified(context,'fixture-store','support','policy',lambda **kw:[seal(document,key)],key)
    with TemporaryDirectory() as temp:
        chain=AuditChain(Path(temp)/'audit.jsonl')
        anchor=chain.append(AuditEvent(request_id=context.request_id,session_id=context.session_id,user_role=context.role,confidence=0,latency_ms=0,documents_retrieved=[document.document_id],final_status='success'))
        print(json.dumps({'fixture':True,'verified_documents':len(results),'audit_anchor':verify_chain(chain.read(),anchor),'secrets_printed':False},indent=2))
if __name__=='__main__':main()
