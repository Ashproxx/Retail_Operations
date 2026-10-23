import math
import pytest
from app.auxiliary.retrieval import LexicalEmbedder, retrieval_metrics


def test_metrics_use_positive_denominator_and_all_abstentions():
    positives=[{'expected':'A','ranked':['A'],'status':'evidence_found'},
        {'expected':'B','ranked':['X','B'],'status':'insufficient_evidence'},
        {'expected':'C','ranked':['X'],'status':'insufficient_evidence'}]
    negatives=[{'status':'insufficient_evidence'},{'status':'evidence_found'}]
    m=retrieval_metrics(positives,negatives)
    assert m['recall_at_3']==2/3 and m['mrr_at_3']==.5
    assert m['ndcg_at_3']==pytest.approx((1+1/math.log2(3))/3)
    assert m['abstention_precision']==1/3 and m['negative_abstention_rate']==.5
    with pytest.raises(ValueError):retrieval_metrics([],negatives)


def test_embedding_vocabulary_is_document_only():
    embedder=LexicalEmbedder(['return clothing with receipt','track delivery order'])
    before=dict(embedder.vectorizer.vocabulary_)
    assert not any(embedder.encode(['unseenword'])[0])
    assert embedder.vectorizer.vocabulary_==before


def test_persistent_store_releases_windows_files():
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from app.rag.store import ChromaStore
    from app.rag.contracts import Document
    from app.rag.ingestion import chunk_document
    from app.rag.contracts import RagSettings
    with TemporaryDirectory() as folder:
        store=ChromaStore(Path(folder)/'chroma',LexicalEmbedder(['return clothing with receipt']))
        try:
            document=Document(document_id='test',version='1',source='fixture://test',domain='support',
                              access_tag='FIXTURE',text='return clothing with receipt',fixture=True)
            store.add(chunk_document(document,RagSettings()))
            assert store.count()==1
        finally:store.client.close()
    assert not Path(folder).exists()
