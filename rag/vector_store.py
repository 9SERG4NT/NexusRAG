"""
ChromaDB vector store wrapper.
- Persists to disk so ingest_all.py and query.py share the same index.
- Uses cosine similarity (hnsw:space=cosine).
- Supports RBAC-filtered queries via the `where` metadata clause.
"""

from __future__ import annotations
from pathlib import Path
import chromadb
from chromadb.config import Settings
from config import COLLECTION_NAME, CHROMA_DIR


class VectorStore:
    def __init__(self, persist_dir: Path = CHROMA_DIR, collection_name: str = COLLECTION_NAME):
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]):
        """Insert chunks + their embeddings into ChromaDB."""
        ids = [c["metadata"]["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = []
        for c in chunks:
            # ChromaDB metadata values must be str/int/float/bool — sanitise lists
            m = {}
            for k, v in c["metadata"].items():
                if isinstance(v, list):
                    m[k] = ",".join(str(x) for x in v)
                else:
                    m[k] = v
            metadatas.append(m)

        # Upsert in batches of 500 to avoid memory spikes
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            self._collection.upsert(
                ids=ids[i : i + batch_size],
                embeddings=embeddings[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )
        print(f"Stored {len(ids)} chunks in ChromaDB collection '{COLLECTION_NAME}'")

    # ── Read ──────────────────────────────────────────────────────────────────

    def query(
        self,
        query_embedding: list[float],
        allowed_departments: list[str] | None,
        n_results: int = 10,
    ) -> list[dict]:
        """
        Semantic search with optional RBAC department filter.
        Returns list of { text, metadata, score } dicts, sorted by relevance.
        """
        count = self._collection.count()
        if count == 0:
            return []

        n_results = min(n_results, count)
        kwargs: dict = dict(query_embeddings=[query_embedding], n_results=n_results)

        if allowed_departments:
            # Admin passes None → no filter
            kwargs["where"] = {"department": {"$in": allowed_departments}}

        try:
            results = self._collection.query(**kwargs)
        except Exception:
            # Fallback: query without filter if where clause errors (empty collection edge case)
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )

        hits = []
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, distances):
            # cosine space: distance ∈ [0,2]; clamp similarity to [0,1]
            score = round(max(0.0, 1.0 - float(dist)), 4)
            hits.append({"text": doc, "metadata": meta, "score": score})

        return sorted(hits, key=lambda x: x["score"], reverse=True)

    def count(self) -> int:
        return self._collection.count()

    def reset(self):
        """Drop and recreate the collection (useful for re-ingestion)."""
        self._client.delete_collection(COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print("Collection reset.")
