"""
Enterprise RAG Intelligence — Chainlit UI
LLM : Qwen/Qwen2.5-7B-Instruct via HuggingFace Inference API
Guard: AI-based off-topic detection (embedding similarity, no regex)

Login credentials:
  alice / alice123  →  admin      (all departments)
  bob   / bob123    →  hr_staff   (HR + employees)
  carol / carol123  →  finance    (finance + employees)
  dave  / dave123   →  it_ops     (IT + logs + incidents)
  eve   / eve123    →  employee   (HR only)
"""

from __future__ import annotations
import asyncio
import sys
import html as _html
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import chainlit as cl
from rag.pipeline import EnterprisePipeline
from rag.off_topic_guard import EnterpriseGuard

# ── User registry ──────────────────────────────────────────────────────────────

USERS = {
    "alice": {"role": "admin",    "password": "alice123", "emoji": "🔴"},
    "bob":   {"role": "hr_staff", "password": "bob123",   "emoji": "🟡"},
    "carol": {"role": "finance",  "password": "carol123", "emoji": "🟢"},
    "dave":  {"role": "it_ops",   "password": "dave123",  "emoji": "🔵"},
    "eve":   {"role": "employee", "password": "eve123",   "emoji": "⚪"},
}

ROLE_ACCESS = {
    "admin":    "Full access — all departments",
    "hr_staff": "HR policies + employee records",
    "finance":  "Finance reports + employee data",
    "it_ops":   "IT security + system logs + incidents",
    "employee": "HR policies only",
}

CONF_EMOJI = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}

GITHUB_SOURCE_URLS = {
    "hr_policy.pdf":      "https://github.com/9SERG4NT/NexusRAG/blob/main/data/documents/hr_policy.pdf",
    "finance_report.pdf": "https://github.com/9SERG4NT/NexusRAG/blob/main/data/documents/finance_report.pdf",
    "it_security.pdf":    "https://github.com/9SERG4NT/NexusRAG/blob/main/data/documents/it_security.pdf",
    "employees.csv":      "https://github.com/9SERG4NT/NexusRAG/blob/main/data/structured/employees.csv",
    "incidents.csv":      "https://github.com/9SERG4NT/NexusRAG/blob/main/data/structured/incidents.csv",
    "system_logs.json":   "https://github.com/9SERG4NT/NexusRAG/blob/main/data/logs/system_logs.json",
}

# A follow-up MUST (a) reference the previous answer with a pronoun/anaphora
# AND (b) request a transformation. New queries that happen to mention "table"
# (e.g. "Show Q4 revenue as a markdown table") are NOT follow-ups.
_REFERENCE_WORDS = {"it", "that", "this", "those", "these"}
_REFORMAT_WORDS  = {
    "format", "reformat", "table", "list", "bullet", "bullets",
    "summarize", "summarise", "rewrite", "rephrase", "elaborate",
    "convert", "restructure", "show",
}

def _is_followup(query: str) -> bool:
    q     = query.lower().strip()
    words = q.replace(".", " ").replace(",", " ").replace("?", " ").split()
    if len(words) > 10:
        return False
    has_reference = any(w in _REFERENCE_WORDS for w in words) \
                    or "above" in q or "previous" in q
    has_reformat  = any(w in _REFORMAT_WORDS for w in words)
    return has_reference and has_reformat

SAMPLE_QUERIES = [
    ("📋  Maternity policy",     "What is the maternity leave policy at Acme Corp?"),
    ("💰  Q4 revenue (table)",   "Show Q4 2024 revenue and department budget allocations as a markdown table."),
    ("🚨  Critical logs (table)", "List all CRITICAL and ERROR log entries as a table with columns: Timestamp, Level, Service, Message."),
    ("👥  Eng salaries (list)",  "List Engineering department employees with their roles and salaries as a numbered list."),
    ("📊  Top 5 earners",        "Who are the top 5 highest-paid employees? Show as a markdown table with rank, name, role, salary."),
    ("🔒  MFA requirements",     "What are the IT password and MFA requirements?"),
]

# ── Pipeline + guard singletons ────────────────────────────────────────────────

_pipeline: EnterprisePipeline | None = None
_guard: EnterpriseGuard | None = None


def get_pipeline() -> EnterprisePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = EnterprisePipeline()
    return _pipeline


def get_guard() -> EnterpriseGuard:
    global _guard
    if _guard is None:
        p = get_pipeline()
        _guard = EnterpriseGuard(embedder=p.embedder, store=p.store)
    return _guard


# ── Auth ───────────────────────────────────────────────────────────────────────

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    user = USERS.get(username.lower())
    if user and password == user["password"]:
        return cl.User(
            identifier=username.lower(),
            metadata={"role": user["role"], "emoji": user["emoji"]},
        )
    return None


# ── Chat start ─────────────────────────────────────────────────────────────────

@cl.on_chat_start
async def on_chat_start():
    user     = cl.user_session.get("user")
    username = user.identifier
    role     = user.metadata.get("role", "unknown")
    emoji    = user.metadata.get("emoji", "⚪")
    access   = ROLE_ACCESS.get(role, "Limited access")

    init_msg = cl.Message(content="⏳ Loading knowledge base...", author="System")
    await init_msg.send()

    # Run blocking model-load + ChromaDB init in a thread — keeps event loop free
    await asyncio.to_thread(get_guard)

    await init_msg.remove()

    # Build HTML sample-query buttons (fire via JS → real user message bubble)
    sq_btns = "".join(
        f'<button class="sq-btn" data-query="{_html.escape(q)}">'
        f'<span class="sq-ico">{lbl.split()[0]}</span>'
        f'<span class="sq-lbl">{_html.escape(" ".join(lbl.split()[1:]))}</span>'
        f'</button>'
        for lbl, q in SAMPLE_QUERIES
    )
    sq_panel = f'<div class="sq-grid">{sq_btns}</div>'

    welcome = f"""## {emoji} Welcome to **NexusRAG**, {username.capitalize()}!

| | |
|---|---|
| **Role** | `{role}` |
| **Access** | {access} |
| **LLM** | Qwen/Qwen2.5-7B-Instruct |
| **Sources** | PDFs · CSV · JSON logs |

---
I answer questions **only** about Acme Corp enterprise data.
Off-topic queries are automatically detected by the AI relevance guard.

👇 **Click a sample query to get started:**

{sq_panel}"""

    await cl.Message(content=welcome, author="NexusRAG").send()


# ── Main message handler ───────────────────────────────────────────────────────

@cl.on_message
async def on_message(message: cl.Message):
    await handle_query(message.content.strip())


def _build_footer(result: dict, emoji: str, role: str) -> str:
    conf       = result.get("confidence", 0.0)
    conf_label = result.get("confidence_label", "LOW")
    conf_e     = CONF_EMOJI.get(conf_label, "⚪")
    all_cites  = result.get("citations") or result.get("all_retrieved_sources", [])

    seen: set[str] = set()
    rows: list[str] = []
    for idx, c in enumerate(all_cites[:5], 1):
        src = c.get("source", "unknown")
        if src in seen:
            continue
        seen.add(src)
        url   = GITHUB_SOURCE_URLS.get(src)
        dept  = c.get("department", "?")
        score = float(c.get("score", 0))
        link  = f"[{src}]({url})" if url else f"`{src}`"
        rows.append(f"| {idx} | {link} | `{dept}` | `{score:.3f}` |")

    if rows:
        table = (
            "\n\n### 📚 References\n\n"
            "| # | Source (GitHub) | Department | Relevance |\n"
            "|---|---|---|---|\n"
            + "\n".join(rows)
        )
    else:
        table = ""

    return (
        f"\n\n---\n"
        f"{conf_e} **Confidence:** {conf_label} `{conf:.0%}` | "
        f"{emoji} **Role:** `{role}` | "
        f"📄 **Sources:** {result.get('sources_used', 0)}"
        f"{table}"
    )


async def _send_result(result: dict, emoji: str, role: str) -> None:
    answer = result.get("answer", "No answer generated.")
    await cl.Message(content=answer + _build_footer(result, emoji, role), author="NexusRAG").send()


async def handle_query(query: str):
    user     = cl.user_session.get("user")
    username = user.identifier
    role     = user.metadata.get("role", "unknown")
    emoji    = user.metadata.get("emoji", "⚪")

    pipeline = get_pipeline()
    guard    = get_guard()

    _GREETING_REPLY = (
        f"👋 Hello, **{username.capitalize()}**! I'm the Acme Corp enterprise assistant.\n\n"
        "Ask me anything about:\n"
        "- 📋 HR policies & leave entitlements\n"
        "- 💰 Financial reports & budgets\n"
        "- 🔒 IT security & system logs\n"
        "- 👥 Employee & incident records\n\n"
        "Or click one of the **sample queries** in the welcome message to get started."
    )

    # ── Instant fast-path: unambiguous one-word social tokens (no embedding) ──
    _INSTANT_GREETINGS = {
        "hi", "hello", "hey", "howdy", "greetings", "hiya",
        "thanks", "thank", "ty", "bye", "goodbye", "ciao",
        "ok", "okay", "sure", "yep", "nope", "yes", "no",
    }
    if query.lower().strip("!?., ") in _INSTANT_GREETINGS:
        await cl.Message(content=_GREETING_REPLY, author="NexusRAG").send()
        return

    # ── Follow-up / reformatting request (reuse previous answer, skip RAG) ────
    last_result = cl.user_session.get("last_result")
    if last_result and _is_followup(query):
        prev_answer = last_result.get("answer", "")
        prev_citations = last_result.get("citations") or last_result.get("all_retrieved_sources", [])
        if prev_answer:
            async with cl.Step(name="🔄 Reformatting previous answer", type="tool") as step:
                step.output = f"Follow-up detected — reusing {len(prev_citations)} prior citation(s)"
            result = await asyncio.to_thread(
                pipeline.generator.generate_followup,
                query, prev_answer, prev_citations, username, role,
            )
            cl.user_session.set("last_result", result)
            await _send_result(result, emoji, role)
            return

    # ── Greeting / chitchat shortcut (very short social messages, needs guard) ─
    if len(query.split()) <= 4:
        async with cl.Step(name="🛡️ Checking relevance", type="tool") as step:
            off_topic, top_score = guard.is_off_topic(query)
            from rag.off_topic_guard import OFF_TOPIC_THRESHOLD
            step.output = f"KB similarity: **{top_score:.3f}** | Threshold: **{OFF_TOPIC_THRESHOLD:.3f}** | Result: {'GREETING' if off_topic else 'RELEVANT'}"

        if off_topic:
            await cl.Message(content=_GREETING_REPLY, author="NexusRAG").send()
            return

    # ── AI-based off-topic detection (full queries) ───────────────────────────
    async with cl.Step(name="🛡️ Checking relevance", type="tool") as step:
        off_topic, top_score = guard.is_off_topic(query)
        from rag.off_topic_guard import OFF_TOPIC_THRESHOLD
        step.output = f"Max KB similarity: **{top_score:.3f}** | Threshold: **{OFF_TOPIC_THRESHOLD:.3f}** | Result: {'OFF-TOPIC' if off_topic else 'RELEVANT'}"

    if off_topic:
        await cl.Message(
            content=(
                f"⛔ **Off-topic query detected** *(similarity score: {top_score:.3f})*\n\n"
                "I'm an **enterprise knowledge assistant** for Acme Corp. "
                "I can only answer questions about company data — not general programming, "
                "math, or unrelated topics.\n\n"
                "Try one of the suggested enterprise queries instead."
            ),
            author="NexusRAG",
        ).send()
        return

    # ── Retrieval (RBAC + hybrid search) ─────────────────────────────────────
    async with cl.Step(name="🔍 Retrieving context", type="retrieval") as step:
        retrieve_data = await asyncio.to_thread(pipeline.retrieve_only, username, query)
        info = retrieve_data.get("retrieval_info", {})
        step.output = (
            f"**Allowed depts:** {info.get('allowed_departments', [])}\n"
            f"**Preferred dept:** {info.get('preferred_department') or 'auto'}\n"
            f"**Chunks retrieved:** {info.get('final_chunks', 0)}\n"
            f"**Hybrid scores:** {[round(s, 3) for s in info.get('top_scores', [])]}"
        )

    # ── RBAC access denied ────────────────────────────────────────────────────
    if retrieve_data.get("access_denied"):
        await cl.Message(
            content=f"🔒 **Access Denied**\n\n{retrieve_data['answer']}",
            author="NexusRAG",
        ).send()
        return

    chunks        = retrieve_data["chunks"]
    retrieval_info = retrieve_data["retrieval_info"]

    # ── Generation: get full answer in thread, then stream everything ────────
    raw_answer = await asyncio.to_thread(pipeline.generator.generate_raw, query, chunks)
    result     = pipeline.generator.build_result(raw_answer, chunks, username, role, retrieval_info)
    cl.user_session.set("last_result", result)

    # Combine answer + footer so both stream together (guaranteed to render)
    full_output = raw_answer + _build_footer(result, emoji, role)

    msg = cl.Message(content="", author="NexusRAG")
    await msg.send()
    # Stream in small 4-char chunks for smooth ChatGPT-style typewriter effect
    chunk_size = 4
    for i in range(0, len(full_output), chunk_size):
        await msg.stream_token(full_output[i:i + chunk_size])
        await asyncio.sleep(0.012)
