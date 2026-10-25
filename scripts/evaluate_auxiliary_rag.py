"""Exercise existing signed RAG without network calls or model downloads."""
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
from tempfile import TemporaryDirectory
from app.api.schemas import RequestContext
from app.auxiliary.retrieval import LexicalEmbedder, retrieval_metrics
from app.integration.repository import Repository
from app.integration.rag import SignedRag, VerifiedStore
from app.rag.contracts import Document
from app.rag.store import ChromaStore
from app.services.database_service import Database


def main():
    output=Path('docs/auxiliary/RAG_RESULTS.json')
    if output.exists():raise SystemExit('Refusing to overwrite frozen retrieval results')
    raw=Path('docs/auxiliary/RAG_FIXTURE.json').read_bytes()
    dataset=json.loads(raw)
    embedder=LexicalEmbedder([r['text'] for r in dataset['documents']])
    with TemporaryDirectory() as folder:
        root=Path(folder);db=Database('sqlite:///'+(root/'evaluation.db').as_posix());Repository(db)
        store=None
        try:
            store=ChromaStore(root/'chroma',embedder)
            service=SignedRag(db,secrets.token_bytes(32),store)
            admin=RequestContext(session_id='evaluation',principal_id='fixture-admin',role='ADMIN')
            user=RequestContext(session_id='evaluation',principal_id='fixture-support',role='SUPPORT_AGENT',store_ids=['FIXTURE'])
            for row in dataset['documents']:
                service.ingest(Document(document_id=row['id'],version='1',source='fixture://'+row['id'],
                    domain='support',access_tag='FIXTURE',text=row['text'],fixture=True),admin)
            service.ingest(Document(document_id='forbidden-store',version='1',source='fixture://forbidden',
                domain='support',access_tag='OTHER',text=' '.join(q['question'] for q in dataset['queries']),fixture=True),admin)
            positives=[];negatives=[]
            for row in dataset['queries']:
                hits,rejected=VerifiedStore(service,user,'FIXTURE','support').retrieve(row['question'],'FIXTURE','support',3)
                result=service.query(row['question'],user,'FIXTURE','support')
                if any(h.chunk.access_tag!='FIXTURE' for h in [*hits,*result.sources]):
                    raise RuntimeError('Scope leak detected; benchmark failed')
                positives.append({'id':row['id'],'expected':row['relevant_id'],
                    'ranked':[h.chunk.document_id for h in hits], 'status':result.status,
                    'iterations':result.iterations,'integrity_rejections':rejected})
            for question in dataset['unanswerable']:
                result=service.query(question,user,'FIXTURE','support')
                if any(h.chunk.access_tag!='FIXTURE' for h in result.sources):
                    raise RuntimeError('Scope leak detected; benchmark failed')
                negatives.append({'question':question,'status':result.status})
            report={'status':'MEASURED_AUTHORED_FIXTURE','human_reviewed':False,
                'embedder':embedder.identity,'fixture_sha256':hashlib.sha256(raw).hexdigest(),
                'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                'metrics':retrieval_metrics(positives,negatives),'scope_leaks':0,
                'positive_results':positives,'negative_results':negatives,
                'limitations':['Lexical TF-IDF baseline, not pretrained semantic embedding performance.',
                    '50 authored positives and 15 negatives across 10 invented policy documents; not human reviewed.',
                    'No held-out natural query distribution, parameter tuning, or deployment-quality claim.',
                    'Pipeline evidence-found status does not establish answer correctness or entailment.',
                    'Abstention and ranking are measured separately; failures are retained without changing labels.']}
            output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
            print(json.dumps(report['metrics'],indent=2))
        finally:
            try:
                if store is not None:store.client.close()
            finally:db.close()


if __name__=='__main__':main()
