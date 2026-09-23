"""Measure pretrained retrieval on labelled synthetic data without production claims."""
import argparse
import json
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory
from app.api.schemas import RequestContext
from app.integration.repository import Repository
from app.integration.rag import SignedRag,VerifiedStore
from app.rag.contracts import Document
from app.rag.embeddings import LocalSentenceTransformer
from app.rag.store import ChromaStore
from app.services.database_service import Database

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model-path',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    spec=json.loads(Path('evaluation/models.json').read_text())['embedding']
    dataset=json.loads(Path('evaluation/retail_rag_fixture.json').read_text())
    model=LocalSentenceTransformer(str(args.model_path),spec['repository']+'@'+spec['revision'])
    with TemporaryDirectory() as temporary:
        root=Path(temporary);db=Database('sqlite+pysqlite:///'+str(root/'evaluation.db'));Repository(db)
        try:
            service=SignedRag(db,secrets.token_bytes(32),ChromaStore(root/'chroma',model))
            admin=RequestContext(session_id='evaluation',principal_id='fixture-admin',role='ADMIN')
            user=RequestContext(session_id='evaluation',principal_id='fixture-support',role='SUPPORT_AGENT',store_ids=['FIXTURE'])
            for row in dataset['documents']:
                service.ingest(Document(document_id=row['id'],version='1',source='fixture://'+row['id'],
                    domain='support',access_tag='FIXTURE',text=row['text'],fixture=True),admin)
            service.ingest(Document(document_id='forbidden-store',version='1',source='fixture://forbidden',domain='support',
                access_tag='OTHER',text=' '.join(q['question'] for q in dataset['queries']),fixture=True),admin)
            results=[]
            for q in dataset['queries']:
                hits,rejected=VerifiedStore(service,user,'FIXTURE','support').retrieve(q['question'],'FIXTURE','support',3)
                ranked=[h.chunk.document_id for h in hits]
                assert all(h.chunk.access_tag=='FIXTURE' for h in hits)
                pipeline=service.query(q['question'],user,'FIXTURE','support')
                results.append({'question':q['question'],'expected':q['relevant_id'],'ranked':ranked,
                    'top1_correct':bool(ranked) and ranked[0]==q['relevant_id'],'recall_at_3':q['relevant_id'] in ranked,
                    'pipeline_status':pipeline.status,'iterations':pipeline.iterations,'integrity_rejections':rejected})
            negatives=[{'question':q,'status':service.query(q,user,'FIXTURE','support').status} for q in dataset['unanswerable']]
            report={'fixture':True,'model':spec,'queries':len(results),'top1_accuracy':sum(r['top1_correct'] for r in results)/len(results),
                'recall_at_3':sum(r['recall_at_3'] for r in results)/len(results),
                'pipeline_answers':sum(r['pipeline_status']=='evidence_found' for r in results),
                'unanswerable_abstentions':sum(r['status']=='insufficient_evidence' for r in negatives),
                'scope_leaks':0,'results':results,'unanswerable':negatives,
                'limitations':'12 authored positive queries and 2 negatives; no held-out production distribution, calibration or generalization claim.'}
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps({k:v for k,v in report.items() if k not in {'results','unanswerable'}}))
            if report['top1_accuracy']<.8 or report['recall_at_3']<.9 or report['unanswerable_abstentions']!=len(negatives):
                raise SystemExit('Development retrieval gate failed; inspect the measured report without tuning labels to results.')
        finally:db.close()

if __name__=='__main__':main()
