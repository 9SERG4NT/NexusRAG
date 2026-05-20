"""
Sentence-transformers embedder with lazy singleton loading.
"""

from __future__ import annotations
from functools import lru_cache
from config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _load_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    print(f"Loading embedding model: {model_name} …")
    return SentenceTransformer(model_name)


class Embedder:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name

    @property
    def model(self):
        return _load_model(self.model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Batch embed a list of strings. Returns list of float vectors."""
        vecs = self.model.encode(texts, show_progress_bar=True, batch_size=32)
        return vecs.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        return self.model.encode([text], show_progress_bar=False)[0].tolist()
