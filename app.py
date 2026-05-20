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

SAMPLE_QUERIES = [
    ("📋  Maternity leave policy",       "What is the maternity leave policy at Acme Corp?"),
    ("💰  Q4 revenue & budgets",         "What was the Q4 2024 total revenue and how are the department budgets allocated?"),
    ("🚨  Critical errors in logs",      "Show me all critical and error level entries from the system logs"),
    ("👥  Engineering salaries",         "Show me employee salaries in the Engineering department"),
    ("🏠  Remote work policy",           "What is the remote work policy? How many days per week are allowed?"),
    ("🔒  Password & MFA requirements",  "What are the IT password policy and MFA requirements?"),
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

    # ── Retrieval step ────────────────────────────────────────────────────────
    async with cl.Step(name="🔍 Retrieving context", type="retrieval") as step:
        result = pipeline.query(user=username, query=query)
        info   = result.get("retrieval_info", {})
        step.output = (
            f"**Allowed depts:** {info.get('allowed_departments', [])}\n"
            f"**Preferred dept:** {info.get('preferred_department') or 'auto'}\n"
            f"**Chunks retrieved:** {info.get('final_chunks', 0)}\n"
            f"**Hybrid scores:** {[round(s, 3) for s in info.get('top_scores', [])]}"
        )

    # ── RBAC access denied ────────────────────────────────────────────────────
    if result.get("access_denied"):
        await cl.Message(
            content=f"🔒 **Access Denied**\n\n{result['answer']}",
            author="NexusRAG",
        ).send()
        return

    # ── Build citation side-elements ──────────────────────────────────────────
    elements: list[cl.Text] = []
    all_cites = result.get("citations") or result.get("all_retrieved_sources", [])
    for c in all_cites[:5]:
        elements.append(
            cl.Text(
                name=f"[{c['id']}] {c['source']}",
                content=(
                    f"**File:** `{c['source']}`\n"
                    f"**Format:** {c.get('type', '?').upper()}\n"
                    f"**Department:** `{c.get('department', '?')}`\n"
                    f"**Relevance score:** {float(c.get('score', 0)):.3f}"
                ),
                display="side",
            )
        )

    # ── Final response ────────────────────────────────────────────────────────
    conf       = result.get("confidence", 0.0)
    conf_label = result.get("confidence_label", "LOW")
    conf_e     = CONF_EMOJI.get(conf_label, "⚪")
    answer     = result.get("answer", "No answer generated.")

    footer = (
        f"\n\n---\n"
        f"{conf_e} **Confidence:** {conf_label} `{conf:.0%}` &nbsp;|&nbsp; "
        f"{emoji} **Role:** `{role}` &nbsp;|&nbsp; "
        f"📄 **Sources:** {result.get('sources_used', 0)}"
    )

    await cl.Message(
        content=answer + footer,
        elements=elements,
        author="NexusRAG",
    ).send()
