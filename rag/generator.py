"""
LLM answer generator.
- Builds a strictly grounded prompt (no hallucination).
- Extracts citation references from the answer.
- Computes a confidence score from retrieval signal strength.
- Falls back gracefully when no context is available.
"""

from __future__ import annotations
import re
import os


SYSTEM_PROMPT = """You are a secure enterprise knowledge assistant.

Rules (non-negotiable):
1. Answer ONLY using the provided context. Do NOT use outside knowledge.
2. Cite every fact with [Source N] notation immediately after the statement.
3. If the context does not contain the answer, respond EXACTLY with:
   "I don't have sufficient information in the available sources to answer this question."
4. Never reveal information about other users, their roles, or data they are not authorised to access.
5. Be concise and professional."""

USER_TEMPLATE = """Context:
{context}

Question: {question}

Instructions: Answer using only the context above. Use [Source N] citations after each fact.
If the answer isn't in the context, say so explicitly — do not guess."""


def _build_context_block(chunks: list[dict]) -> tuple[str, list[dict]]:
    """Format retrieved chunks into numbered context block + citation list."""
    lines = []
    citations = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk["metadata"]
        header = f"[Source {i}: {meta.get('source', 'unknown')} | {meta.get('source_type','?').upper()} | dept={meta.get('department','?')}]"
        lines.append(f"{header}\n{chunk['text']}")
        citations.append({
            "id": i,
            "source": meta.get("source", "unknown"),
            "type": meta.get("source_type", "unknown"),
            "department": meta.get("department", "unknown"),
            "chunk_id": meta.get("chunk_id", ""),
            "score": chunk.get("hybrid_score", chunk.get("score", 0)),
        })
    return "\n\n".join(lines), citations


def _compute_confidence(chunks: list[dict]) -> float:
    """Confidence based on top retrieval score + number of supporting chunks.
    Normalized against SIMILARITY_THRESHOLD so any valid answer starts at ≥ MEDIUM.
    """
    if not chunks:
        return 0.0
    from config import SIMILARITY_THRESHOLD as T
    top  = chunks[0].get("hybrid_score", chunks[0].get("score", 0))
    cov  = min(len(chunks) / 5.0, 1.0)
    # Normalise score: 0 at threshold, 1 at perfect match
    norm = max(0.0, min((top - T) / (1.0 - T), 1.0))
    # Floor at 0.40 so any answer that passed the guard reaches ≥ MEDIUM with 2+ chunks
    return round(min(0.40 + 0.60 * (0.70 * norm + 0.30 * cov), 1.0), 3)


def _call_anthropic(system: str, user_msg: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return message.content[0].text


def _call_openai(system: str, user_msg: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=1024,
        temperature=0.0,
    )
    return resp.choices[0].message.content


def _call_hf(system: str, user_msg: str, model: str, token: str) -> str:
    """Call HuggingFace Inference API (supports Gemma, Mistral, etc.)."""
    from huggingface_hub import InferenceClient
    client = InferenceClient(api_key=token)
    # Gemma-2 supports system role via its chat template
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_msg},
    ]
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.1,
        )
        return completion.choices[0].message.content
    except Exception as e:
        # Some Gemma variants don't accept system role — merge into user turn
        merged = f"{system}\n\n{user_msg}"
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": merged}],
            max_tokens=1024,
            temperature=0.1,
        )
        return completion.choices[0].message.content


def _extract_cited_sources(answer: str, citations: list[dict]) -> list[dict]:
    """Return only citations that are actually referenced in the answer text."""
    cited_ids = {int(m) for m in re.findall(r"\[Source (\d+)\]", answer)}
    return [c for c in citations if c["id"] in cited_ids]


class Generator:
    def __init__(self, model: str | None = None, provider: str | None = None):
        from config import LLM_PROVIDER, HF_MODEL, LLM_MODEL, HF_TOKEN
        # Provider priority: explicit arg > config > auto-detect from env keys
        if provider:
            self.provider = provider
        else:
            self.provider = LLM_PROVIDER

        if self.provider == "hf":
            self.model = model or HF_MODEL
            self.hf_token = HF_TOKEN or os.environ.get("HF_TOKEN", "")
        else:
            self.model = model or LLM_MODEL
            self.hf_token = ""

    def _call_llm(self, system: str, user_msg: str) -> str:
        if self.provider == "hf":
            return _call_hf(system, user_msg, self.model, self.hf_token)
        if self.provider == "anthropic":
            return _call_anthropic(system, user_msg, self.model)
        if self.provider == "openai":
            openai_model = "gpt-4o-mini" if "claude" in self.model else self.model
            return _call_openai(system, user_msg, openai_model)
        # Mock: extract key lines from context for offline testing
        lines = [ln for ln in user_msg.split("\n") if ln.strip() and not ln.startswith("[Source")]
        snippet = " ".join(lines[:3])[:300]
        return f"[MOCK — no API key configured] Based on context: {snippet} [Source 1]"

    def generate(
        self,
        query: str,
        chunks: list[dict],
        username: str,
        role: str,
        retrieval_info: dict | None = None,
    ) -> dict:
        if not chunks:
            return {
                "answer": "I don't have sufficient information in the available sources to answer this question.",
                "citations": [],
                "confidence": 0.0,
                "user": username,
                "role": role,
                "sources_used": 0,
                "retrieval_info": retrieval_info or {},
            }

        context_text, citations = _build_context_block(chunks)
        user_msg = USER_TEMPLATE.format(context=context_text, question=query)

        answer = self._call_llm(SYSTEM_PROMPT, user_msg)

        cited = _extract_cited_sources(answer, citations)
        confidence = _compute_confidence(chunks)

        return {
            "answer": answer,
            "citations": cited,
            "all_retrieved_sources": citations,
            "confidence": confidence,
            "confidence_label": _confidence_label(confidence),
            "user": username,
            "role": role,
            "sources_used": len(cited) or len(chunks),
            "retrieval_info": retrieval_info or {},
        }


def _confidence_label(score: float) -> str:
    if score >= 0.75:  return "HIGH"
    if score >= 0.45:  return "MEDIUM"
    return "LOW"
