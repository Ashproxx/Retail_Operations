"""Authorize before Chroma; verify a separately signed manifest before evidence use."""
import hashlib
import hmac
from threading import RLock
from app.api.schemas import Role
from app.security.policy import authorize, AccessDenied
from app.security.integrity import canonical, IntegrityFailure
from app.core.exceptions import ComponentUnavailableError, DataValidationError
from app.rag.ingestion import chunk_document
from app.rag.contracts import RagSettings
from app.rag.pipeline import RagPipeline
from app.integration.repository import ManifestRow

DOMAIN_ACTIONS={'inventory':'inventory.read','forecasting':'forecast.read','analytics':'analytics.read',
                'pricing':'pricing.recommend','orders':'orders.read','supply':'supply.read',
                'support':'support.read','returns':'returns.read'}

class VerifiedStore:
    def __init__(self, service, context, store_id, domain):
        self.service,self.context,self.store_id,self.domain=service,context,store_id,domain
    def count(self):
        authorize(self.context,DOMAIN_ACTIONS[self.domain],self.store_id)
        return self.service.store.count()
    def retrieve(self, query, access_tag, domain, top_k):
        if access_tag!=self.store_id or domain!=self.domain:raise AccessDenied('Scope mismatch')
        authorize(self.context,DOMAIN_ACTIONS[domain],access_tag)
        hits,rejected=self.service.store.retrieve(query,access_tag,domain,top_k)
        verified=[]
        with self.service.database.session() as session:
            for hit in hits:
                chunk=hit.chunk
                row=session.get(ManifestRow,chunk.chunk_id)
                expected=self.service.signature(chunk)
                if (chunk.access_tag!=access_tag or chunk.domain!=domain or row is None
                        or not hmac.compare_digest(row.signature,expected)):
                    rejected+=1
                else:verified.append(hit)
        return verified,rejected

class SignedRag:
    def __init__(self,database,key:bytes,store,settings=None):
        if len(key)<32:raise ValueError('Use an integrity key of at least 32 bytes')
        self.database,self.key,self.store=database,key,store
        self.settings=settings or RagSettings()
        self.lock=RLock()
    def signature(self,chunk):
        return hmac.new(self.key,canonical(chunk.model_dump(mode='json')),hashlib.sha256).hexdigest()
    def ingest(self,document,context):
        if context.role!=Role.ADMIN:raise AccessDenied('Only administrators ingest approved documents')
        if document.domain not in DOMAIN_ACTIONS:raise DataValidationError('Unknown RAG domain')
        authorize(context,DOMAIN_ACTIONS[document.domain],document.access_tag)
        chunks=chunk_document(document,self.settings)
        with self.lock:
            # Refuse revision mutation before either persistence layer changes.
            with self.database.session() as session:
                for chunk in chunks:
                    previous=session.get(ManifestRow,chunk.chunk_id)
                    if previous and not hmac.compare_digest(previous.signature,self.signature(chunk)):
                        raise IntegrityFailure('Immutable signed revision changed')
            count=self.store.add(chunks)
            # A crash before this commit leaves chunks untrusted, so retrieval fails closed.
            with self.database.session() as session:
                for chunk in chunks:session.merge(ManifestRow(chunk_id=chunk.chunk_id,signature=self.signature(chunk)))
            return count
    def query(self,question,context,store_id,domain):
        if domain not in DOMAIN_ACTIONS:raise DataValidationError('Unknown RAG domain')
        authorize(context,DOMAIN_ACTIONS[domain],store_id)
        with self.lock:
            return RagPipeline(VerifiedStore(self,context,store_id,domain),self.settings).query(question,access_tag=store_id,domain=domain)

class LazyRag:
    def __init__(self,database,config):
        self.database,self.config=database,config
        self.service=None
        self.lock=RLock()
    def get(self):
        with self.lock:
            if self.service is None:
                config=self.config
                if not config.integrity_key or not config.embedding_model_path or not config.embedding_identity:
                    raise ComponentUnavailableError('Configure local embeddings and an integrity key')
                from app.rag.embeddings import LocalSentenceTransformer
                from app.rag.store import ChromaStore
                model=LocalSentenceTransformer(str(config.embedding_model_path),config.embedding_identity)
                store=ChromaStore(config.state_dir/'chroma',model)
                self.service=SignedRag(self.database,config.integrity_key.get_secret_value().encode(),store,
                                       RagSettings(max_iterations=config.max_rag_iterations))
            return self.service
    def query(self,question,context,store_id,domain):
        if domain not in DOMAIN_ACTIONS:raise DataValidationError('Unknown domain')
        authorize(context,DOMAIN_ACTIONS[domain],store_id)
        return self.get().query(question,context,store_id,domain)
    def ingest(self,document,context):
        if context.role!=Role.ADMIN:raise AccessDenied('Only administrators ingest documents')
        return self.get().ingest(document,context)
