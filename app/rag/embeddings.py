"""Local CPU embeddings. Models must already exist on disk."""
from pathlib import Path
from typing import Protocol


class Embedder(Protocol):
    identity: str
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class LocalSentenceTransformer:
    def __init__(self, model_path: str, identity: str):
        if not Path(model_path).is_dir():
            raise ValueError("Local embedding model directory is missing")
        if not identity.strip():
            raise ValueError("Pin an embedding model identity/version")
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_path, device="cpu", local_files_only=True,
                                         trust_remote_code=False)
        self.identity = identity

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()
