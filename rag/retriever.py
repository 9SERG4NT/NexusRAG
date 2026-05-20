"""
Hybrid retriever: semantic search (ChromaDB) + BM25 keyword re-ranking
with query-aware source boosting.
"""

from __future__ import annotations
from rank_bm25 import BM25Okapi
from config import TOP_K_RETRIEVE, TOP_K_FINAL, SIMILARITY_THRESHOLD
from rag.rbac import RBACGuard
from rag.embedder import Embedder
from rag.vector_store import VectorStore


# ── Query-aware routing boosts ────────────────────────────────────────────────

QUERY_BOOSTS: list[tuple[list[str], str]] = [
    (["log", "error", "alert", "critical", "warning", "outage", "incident report"], "logs"),
    (["policy", "leave", "maternity", "paternity", "remote work", "conduct", "hr", "vacation", "holiday"], "hr"),
    (["salary", "payroll", "revenue", "budget", "financial", "profit", "expense", "fiscal"], "finance"),
    (["password", "vpn", "security", "compliance", "audit", "certificate", "breach", "vulnerability"], "it"),
    (["employee", "staff", "hire", "department", "headcount", "team"], "employees"),
    (["incident", "severity", "p1", "p2", "p3", "ticket", "jira"], "incidents"),
]


def detect_preferred_source(query: str) -> str | None:
    """Returns the department tag most relevant to this query, if any."""
    q = query.lower()
    for keywords, dept in QUERY_BOOSTS:
        if any(kw in q for kw in keywords):
            return dept
    return None


def bm25_rerank(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    """Re-rank semantic candidates using BM25 on their text, return top_k."""
    if not candidates:
        return []
    tokenized = [c["text"].lower().split() for c in candidates]
    bm25 = BM25Okapi(tokenized)
    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)
    # Combine: 0.6 * semantic_score + 0.4 * bm25_normalised
    max_bm25 = max(scores) if max(scores) > 0 else 1.0
    for i, c in enumerate(candidates):
        bm25_norm = scores[i] / max_bm25
        c["hybrid_score"] = round(0.6 * c["score"] + 0.4 * bm25_norm, 4)
    ranked = sorted(candidates, key=lambda x: x["hybrid_score"], reverse=True)
    return ranked[:top_k]


class HybridRetriever:
    def __init__(self, rbac: RBACGuard, embedder: Embedder, store: VectorStore):
        self.rbac = rbac
        self.embedder = embedder
        self.store = store

    def retrieve(
        self,
        query: str,
        username: str,
        top_k: int = TOP_K_FINAL,
    ) -> tuple[list[dict], dict]:
        """
        Returns (chunks, retrieval_info):
          - chunks: list of { text, metadata, score, hybrid_score }
          - retrieval_info: debug/trace dict for explainability
        """
        info: dict = {"user": username, "query": query}

        # ── 1. Resolve RBAC permissions ───────────────────────────────────────
        allowed = self.rbac.get_allowed_departments(username)
        if allowed is None:
            return [], {"error": f"Unknown user: {username}"}
        info["role"] = self.rbac.get_user_role(username)
        info["allowed_departments"] = allowed

        # Admin: no department filter (pass None to store.query)
        dept_filter = None if self.rbac.is_admin(username) else allowed

        # ── 2. Detect preferred source type from query keywords ───────────────
        preferred_dept = detect_preferred_source(query)
        info["preferred_department"] = preferred_dept

        # ── 3. Semantic search ────────────────────────────────────────────────
        query_vec = self.embedder.embed_query(query)
        candidates = self.store.query(query_vec, dept_filter, n_results=TOP_K_RETRIEVE)

        # ── 4. Apply similarity threshold ─────────────────────────────────────
        candidates = [c for c in candidates if c["score"] >= SIMILARITY_THRESHOLD]

        # ── 5. Boost preferred source score (persists through BM25 re-rank) ─────
        if preferred_dept:
            for c in candidates:
                if c["metadata"].get("department") == preferred_dept:
                    c["score"] = min(c["score"] * 1.30, 1.0)
            candidates.sort(key=lambda x: x["score"], reverse=True)

        # ── 6. BM25 re-rank ───────────────────────────────────────────────────
        ranked = bm25_rerank(query, candidates, top_k=top_k)

        # ── 7. Final RBAC hard filter (belt-and-suspenders) ───────────────────
        ranked = self.rbac.filter_chunks(ranked, username)

        info["candidates_after_threshold"] = len(candidates)
        info["final_chunks"] = len(ranked)
        info["top_scores"] = [c.get("hybrid_score", c["score"]) for c in ranked[:3]]

        return ranked, info
