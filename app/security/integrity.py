"""Standard digest/HMAC checks; no custom cryptographic primitive."""
import hashlib,hmac,json
from pydantic import Field
from app.api.schemas import Contract
from app.core.exceptions import RetailOpsError

class IntegrityFailure(RetailOpsError):
    code='integrity_failure'
    status_code=503

class Document(Contract):
    document_id:str=Field(min_length=1)
    version:str=Field(min_length=1)
    store_id:str=Field(min_length=1)
    domain:str=Field(min_length=1)
    source:str=Field(min_length=1)
    text:str=Field(min_length=1,max_length=200000)

class SealedDocument(Contract):
    document:Document
    sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    signature:str=Field(pattern=r'^[0-9a-f]{64}$')


def canonical(value:dict)->bytes:
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def seal(document:Document,key:bytes)->SealedDocument:
    if len(key)<32:raise ValueError('Use a random key of at least 32 bytes')
    payload=canonical(document.model_dump())
    return SealedDocument(document=document.model_copy(deep=True),sha256=hashlib.sha256(payload).hexdigest(),
                          signature=hmac.new(key,payload,'sha256').hexdigest())


def verify(sealed:SealedDocument,key:bytes)->None:
    expected=seal(sealed.document,key)
    if not hmac.compare_digest(expected.sha256,sealed.sha256) or not hmac.compare_digest(expected.signature,sealed.signature):
        raise IntegrityFailure('Document verification failed')
