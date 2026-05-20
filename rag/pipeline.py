"""
EnterprisePipeline: orchestrates RBAC → retrieval → generation.
Single entry point for both CLI and FastAPI.
"""

from __future__ import annotations
from pathlib import Path
from config import DATA_DIR, CHROMA_DIR, COLLECTION_NAME, TOP_K_FINAL
from rag.rbac import RBACGuard
from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.retriever import HybridRetriever
from rag.generator import Generator


class EnterprisePipeline:
    def __init__(self):
        ac_dir = DATA_DIR / "access_control"
        self.rbac = RBACGuard(
            users_path=ac_dir / "users.json",
            roles_path=ac_dir / "roles.json",
        )
        self.embedder = Embedder()
        self.store = VectorStore(persist_dir=CHROMA_DIR, collection_name=COLLECTION_NAME)
        self.retriever = HybridRetriever(self.rbac, self.embedder, self.store)
        self.generator = Generator()

        # Auto-ingest if the vector store is empty
        if self.store.count() == 0:
            print("Vector store is empty — running auto-ingestion …")
            self._auto_ingest()

    def _auto_ingest(self):
        from rag.ingestor import ingest_all
        chunks = ingest_all(DATA_DIR)
        texts = [c["text"] for c in chunks]
        print(f"Embedding {len(chunks)} chunks …")
        embeddings = self.embedder.embed_documents(texts)
        self.store.add_chunks(chunks, embeddings)
        print(f"Auto-ingestion complete — {self.store.count()} chunks indexed.")

    def query(self, user: str, query: str, top_k: int = TOP_K_FINAL) -> dict:
        """
        Full RAG pipeline for a user query.

        Returns a result dict with:
          answer, citations, confidence, role, user,
          retrieval_info (for traceability)
        """
        # ── Unknown user ──────────────────────────────────────────────────────
        role = self.rbac.get_user_role(user)
        if role is None:
            return {
                "answer": f"Access denied: unknown user '{user}'.",
                "citations": [],
                "confidence": 0.0,
                "user": user,
                "role": None,
                "access_denied": True,
                "reason": "User not found in user registry.",
            }

        # ── RBAC query-level check ────────────────────────────────────────────
        allowed, reason = self.rbac.check_query_access(user, query)
        if not allowed:
            return {
                "answer": f"Access denied: {reason}",
                "citations": [],
                "confidence": 0.0,
                "user": user,
                "role": role,
                "access_denied": True,
                "reason": reason,
            }

        # ── Retrieve ──────────────────────────────────────────────────────────
        chunks, retrieval_info = self.retriever.retrieve(query, user, top_k=top_k)

        # ── Generate ──────────────────────────────────────────────────────────
        result = self.generator.generate(query, chunks, user, role, retrieval_info)
        return result


# Module-level singleton (shared across imports)
_pipeline: EnterprisePipeline | None = None


def get_pipeline() -> EnterprisePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = EnterprisePipeline()
    return _pipeline
