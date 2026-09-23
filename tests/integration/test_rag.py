import hashlib
import secrets
import pytest
from app.integration.rag import SignedRag
from app.integration.repository import Repository,ManifestRow
from app.services.database_service import Database
from app.rag.contracts import Document
from app.rag.store import ChromaStore
from app.rag.ingestion import digest
from app.rag.embeddings import LocalSentenceTransformer
from app.api.schemas import RequestContext
from app.security.policy import AccessDenied
from app.security.integrity import IntegrityFailure
from tests.integration.conftest import headers

@pytest.fixture(scope='module')
def embedder(tmp_path_factory):
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.sentence_transformer import modules as models
    path=tmp_path_factory.mktemp('integration-bow')
    SentenceTransformer(modules=[models.BoW(['customer','service','faq','opening','hours','nine','five','receipt','refund','inventory']),models.Normalize()]).save(str(path))
    return LocalSentenceTransformer(str(path),'integration-fixture-bow-v1')

@pytest.fixture
def service(tmp_path,embedder):
    db=Database('sqlite+pysqlite:///'+str(tmp_path/'rag.db'));Repository(db)
    yield SignedRag(db,secrets.token_bytes(32),ChromaStore(tmp_path/'chroma',embedder))
    db.close()

def context(role='ADMIN',stores=None):
    return RequestContext(session_id='rag',principal_id='test',role=role,store_ids=stores or [])

def doc(**updates):
    return Document(**{'document_id':'fixture-faq','version':'1','access_tag':'BANDRA','domain':'support',
        'source':'fixture://faq','fixture':True,'text':'Customer service FAQ opening hours are nine to five.',**updates})

def test_signed_ingestion_scope_and_retrieval(service):
    service.ingest(doc(),context())
    result=service.query('opening hours',context('SUPPORT_AGENT',['BANDRA']),'BANDRA','support')
    assert result.status=='evidence_found' and result.sources[0].chunk.fixture
    with pytest.raises(AccessDenied):service.query('opening hours',context('ANALYST',['BANDRA']),'BANDRA','support')
    with pytest.raises(AccessDenied):service.query('opening hours',context('SUPPORT_AGENT',['ANDHERI']),'BANDRA','support')
    with pytest.raises(AccessDenied):service.ingest(doc(),context('STORE_MANAGER',['BANDRA']))


def test_rehashed_vector_tampering_fails_signed_manifest(service):
    service.ingest(doc(),context())
    rows=service.store.collection.get(include=['documents','metadatas'])
    meta=rows['metadatas'][0];id=rows['ids'][0]
    text='Opening hours are secret changed policy.'
    meta['content_hash']=digest({**{k:v for k,v in meta.items() if k!='content_hash'},'chunk_id':id,'text':text})
    service.store.collection.update(ids=[id],documents=[text],metadatas=[meta],embeddings=service.store.embedder.encode([text]))
    result=service.query('opening hours',context(),'BANDRA','support')
    assert result.status=='insufficient_evidence' and not result.sources
    assert any(t['rejected'] for t in result.trace)


def test_manifest_mutation_and_immutable_revision(service):
    service.ingest(doc(),context())
    with pytest.raises(IntegrityFailure):service.ingest(doc(text='Changed hours'),context())
    id=service.store.collection.get()['ids'][0]
    with service.database.session() as session:session.get(ManifestRow,id).signature='0'*64
    result=service.query('opening hours',context(),'BANDRA','support')
    assert not result.sources


def test_api_and_support_agent_use_signed_rag(client,service):
    runtime=client.app.state.runtime
    runtime.rag=service;runtime.orchestrator.rag=service
    response=client.post('/api/rag/ingest',headers=headers(),json={'session_id':'s','document':doc().model_dump()})
    assert response.status_code==200,response.text
    response=client.post('/api/chat',headers=headers('manager'),json={'session_id':'s','message':'customer service FAQ opening hours','parameters':{'store_id':'BANDRA'}})
    body=response.json()
    assert body['data']['status']=='success',body
    assert body['sources'][0]['document_id'] in {'FAQ','fixture-faq'}
    result=body['data']['results']['customer-service']
    assert result['data']['rag']['status']=='evidence_found'
    events=runtime.audit.read()
    assert events[-1]['event']['rag_iterations']>=1
