"""Offline fixture demonstration. No production policy or pretrained model."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer import modules
from app.rag.contracts import Document, RagSettings
from app.rag.embeddings import LocalSentenceTransformer
from app.rag.ingestion import chunk_document
from app.rag.store import ChromaStore
from app.rag.pipeline import RagPipeline


def main():
    with TemporaryDirectory() as temp:
        root = Path(temp)
        model_path = root/'model'
        SentenceTransformer(modules=[modules.BoW(['refund','receipt','policy','thirty','days']),
                                     modules.Normalize()]).save(str(model_path))
        embedder = LocalSentenceTransformer(str(model_path), 'fixture-bow-v1')
        store = ChromaStore(root/'chroma', embedder)
        document = Document(document_id='fixture-policy', version='v1', source='fixture://policy',
                            domain='support', access_tag='demo-support', fixture=True,
                            text='Refund policy requires receipt within thirty days.')
        store.add(chunk_document(document, RagSettings()))
        result = RagPipeline(store).query('refund receipt policy', access_tag='demo-support', domain='support')
        print(json.dumps(result.model_dump(), indent=2))


if __name__ == '__main__':
    main()
