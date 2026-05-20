"""
AI-based off-topic guard.

Instead of hardcoded regex / keyword lists, we embed the user query and
check its maximum cosine similarity against the enterprise knowledge base.

If the top similarity is below `threshold`, the query has no semantic
overlap with any document in the KB → treat as off-topic.

This means the guard automatically adapts to whatever data is ingested —
no manual rule maintenance required.
"""

from __future__ import annotations
from config import SIMILARITY_THRESHOLD
from rag.embedder import Embedder
from rag.vector_store import VectorStore

# Slightly lower than retrieval threshold — we want to catch truly unrelated
# queries (Python tutorials, recipe requests, sports scores, etc.) while
# still letting borderline enterprise queries through.
OFF_TOPIC_THRESHOLD = max(SIMILARITY_THRESHOLD - 0.05, 0.15)


class EnterpriseGuard:
    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    def is_off_topic(self, query: str) -> tuple[bool, float]:
        """
        Returns (is_off_topic, top_score).

        Embeds the query and checks max cosine similarity against ALL chunks
        in the knowledge base (no RBAC filter — we're only testing relevance,
        not authorisation; RBAC enforcement happens downstream in the retriever).
        """
        query_vec = self.embedder.embed_query(query)
        results = self.store.query(
            query_embedding=query_vec,
            allowed_departments=None,   # no filter — admin-level scan for topic relevance
            n_results=1,
        )
        if not results:
            return True, 0.0

        top_score = results[0].get("score", 0.0)
        return top_score < OFF_TOPIC_THRESHOLD, round(top_score, 4)
