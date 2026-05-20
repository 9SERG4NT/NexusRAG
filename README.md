---
title: NexusRAG
emoji: 🔐
colorFrom: red
colorTo: gray
sdk: docker
app_file: app.py
pinned: false
---

<div align="center">

# 🔐 NexusRAG — Enterprise Intelligence

**Production-grade Retrieval-Augmented Generation for enterprise knowledge management**

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-HuggingFace_Spaces-FFD21E?style=for-the-badge&logo=huggingface)](https://serg4nt-nexusrag.hf.space)
[![GitHub](https://img.shields.io/badge/GitHub-9SERG4NT%2FNexusRAG-181717?style=for-the-badge&logo=github)](https://github.com/9SERG4NT/NexusRAG)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![Chainlit](https://img.shields.io/badge/Chainlit-2.11.1-FF6B35?style=for-the-badge)](https://chainlit.io)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.3-FF6B6B?style=for-the-badge)](https://trychroma.com)

</div>

---

## 🌐 Live Demo

> **[https://serg4nt-nexusrag.hf.space](https://serg4nt-nexusrag.hf.space)**

Use any of the demo credentials below to log in instantly — no setup required.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Multi-source ingestion** | PDFs · CSV · JSON — chunked, embedded, and indexed at build time |
| **Hybrid retrieval** | ChromaDB semantic search + BM25 re-ranking (0.6 × semantic + 0.4 × BM25) |
| **RBAC** | 5 roles × 7 department scopes enforced at both routing and chunk retrieval |
| **AI off-topic guard** | Embedding cosine similarity vs KB — no hardcoded regex |
| **Instant greetings** | 20-token fast-path bypasses embedding for social messages |
| **Citation tracing** | Every answer cites `[Source N]` with file · department · relevance score |
| **Confidence scoring** | Per-answer HIGH / MEDIUM / LOW with calibrated percentage |
| **LLM** | Qwen/Qwen2.5-7B-Instruct via HuggingFace Inference API |
| **UI** | Chainlit 2.x · dark/light theme · quick-login panel · sample query buttons |

---

## 🏗️ AI Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Chainlit UI)                          │
│   Login Page ──► Quick-login buttons / Manual credentials           │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ POST /login (form-encoded)
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SECURITY LAYER                                │
│                                                                     │
│  1. PASSWORD AUTH  ──  users.json lookup → JWT cookie (HS256)       │
│                                                                     │
│  2. INSTANT FAST-PATH  ──  1-word social token? → greet & return    │
│     {"hi","hello","thanks","bye","ok","yes","no" …} (20 tokens)     │
│                                                                     │
│  3. OFF-TOPIC GUARD  ──  Embed query (all-MiniLM-L6-v2, 384-dim)   │
│     → ChromaDB full-scan (no RBAC filter)                           │
│     → max cosine similarity < 0.20? → ⛔ Reject                    │
│                                                                     │
│  4. RBAC CHECK  ──  role → roles.json → allowed departments         │
│     → query keyword in forbidden dept? → 🔒 Access Denied          │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ passes all checks
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RETRIEVAL ENGINE                               │
│                                                                     │
│  SEMANTIC SEARCH  ──  embed query → ChromaDB cosine search          │
│    · RBAC where-filter: dept IN [allowed_departments]               │
│    · top-10 candidates returned                                     │
│    · score clamped: max(0.0, 1.0 − cosine_distance)                 │
│                                                                     │
│  THRESHOLD FILTER  ──  drop chunks with score < 0.25               │
│                                                                     │
│  DEPT BOOST  ──  keyword → preferred dept → score × 1.30           │
│    (finance→"revenue/budget", hr→"leave/policy",                    │
│     it→"password/VPN", logs→"error/critical")                       │
│                                                                     │
│  BM25 RE-RANK  ──  hybrid_score = 0.6×semantic + 0.4×BM25_norm     │
│    → return top-5 chunks                                            │
│                                                                     │
│  HARD RBAC FILTER  ──  belt-and-suspenders dept re-check            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ top-5 grounded chunks
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     GENERATION ENGINE                               │
│                                                                     │
│  CONTEXT BUILD  ──  number chunks [Source 1]…[Source N]             │
│    header: "[Source N: filename | PDF/CSV/JSON | dept=X]"           │
│                                                                     │
│  LLM CALL  ──  Qwen/Qwen2.5-7B-Instruct (HF Inference API)         │
│    · system prompt: cite [Source N], no hallucination               │
│    · temperature: 0.1 · max_tokens: 1024                            │
│                                                                     │
│  CITATION EXTRACTION  ──  regex scan for [Source N] references      │
│                                                                     │
│  CONFIDENCE SCORE  ──  calibrated formula:                          │
│    norm  = (top_score − 0.25) / 0.75                                │
│    cover = min(chunks / 5, 1.0)                                     │
│    conf  = 0.40 + 0.60 × (0.70×norm + 0.30×cover)                  │
│    HIGH ≥ 0.75 · MEDIUM ≥ 0.45 · LOW < 0.45                        │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FINAL RESPONSE (Chainlit UI)                     │
│                                                                     │
│  · Answer text with inline [Source N] citations                     │
│  · Side panel: citation cards (file · dept · relevance score)       │
│  · Footer: 🟢/🟡/🔴 Confidence % · Role badge · Source count       │
└─────────────────────────────────────────────────────────────────────┘

KNOWLEDGE BASE (ChromaDB — baked into Docker image)
─────────────────────────────────────────────────────
  hr_policy.pdf       → dept: hr        (leave, remote work, conduct, expenses)
  finance_report.pdf  → dept: finance   (Q4 revenue, budgets, OpEx)
  it_security.pdf     → dept: it        (passwords, VPN, compliance)
  employees.csv       → dept: employees (50 rows · salaries · roles · depts)
  incidents.csv       → dept: incidents (30 IT incidents · severity · status)
  system_logs.json    → dept: logs      (100 entries · INFO/WARNING/ERROR/CRITICAL)

  Chunking: 300 words · 50 overlap
  Embedding: all-MiniLM-L6-v2 (384-dim, sentence-transformers)
  Store: ChromaDB cosine similarity space · 41 total chunks
```

---

## 👥 Demo Credentials

| User | Password | Role | Department Access |
|---|---|---|---|
| `alice` | `alice123` | **admin** | All departments (unrestricted) |
| `bob` | `bob123` | **hr_staff** | HR policies + employee records |
| `carol` | `carol123` | **finance** | Finance reports + employee data |
| `dave` | `dave123` | **it_ops** | IT security + system logs + incidents |
| `eve` | `eve123` | **employee** | HR policies only |

Quick-login buttons are available on the sign-in screen — one click fills and submits the form.

---

## 📁 Project Structure

```
enterprise_rag/
├── app.py                   # Chainlit UI · auth · message routing
├── config.py                # Central configuration (env-driven)
├── generate_dataset.py      # Synthetic enterprise data generator
├── ingest_all.py            # Standalone ingestion pipeline
├── requirements.txt
├── Dockerfile               # Builds model + ingests data at build time
│
├── rag/
│   ├── pipeline.py          # EnterprisePipeline orchestrator
│   ├── retriever.py         # HybridRetriever (semantic + BM25)
│   ├── generator.py         # LLM answer generation + confidence scoring
│   ├── vector_store.py      # ChromaDB wrapper (cosine, score clamping)
│   ├── embedder.py          # Sentence-transformer singleton
│   ├── ingestor.py          # PDF / CSV / JSON loaders + chunker
│   ├── rbac.py              # Role-based access control
│   └── off_topic_guard.py   # Embedding-based relevance guard
│
├── data/
│   ├── documents/           # hr_policy.pdf · finance_report.pdf · it_security.pdf
│   ├── structured/          # employees.csv · incidents.csv
│   ├── logs/                # system_logs.json
│   └── access_control/      # users.json · roles.json
│
├── .chainlit/
│   └── config.toml          # UI theme · custom CSS/JS · auth config
│
└── public/
    ├── custom.js            # Quick-login panel · sample-query buttons
    └── custom.css           # NexusRAG theme overrides
```

---

## ⚙️ Configuration

Key settings in [`config.py`](config.py):

| Setting | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `"hf"` | `hf` · `openai` · `anthropic` · `mock` |
| `HF_MODEL` | `Qwen/Qwen2.5-7B-Instruct` | HuggingFace model for generation |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer for embeddings |
| `SIMILARITY_THRESHOLD` | `0.25` | Minimum cosine score to keep a chunk |
| `TOP_K_RETRIEVE` | `10` | Candidates fetched from ChromaDB |
| `TOP_K_FINAL` | `5` | Chunks passed to LLM after BM25 re-rank |
| `CHUNK_SIZE` | `300` | Words per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between adjacent chunks |

---

## 🚀 Local Setup

```bash
git clone https://github.com/9SERG4NT/NexusRAG.git
cd NexusRAG

pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env — fill in HF_TOKEN and CHAINLIT_AUTH_SECRET

# Generate synthetic dataset (first run only)
python generate_dataset.py

# Ingest into ChromaDB (first run only)
python ingest_all.py

# Launch
chainlit run app.py --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** and log in with any demo credential.

---

## ☁️ HuggingFace Spaces Deployment

The Docker image pre-bakes everything at build time:
- `all-MiniLM-L6-v2` embedding model downloaded during `docker build`
- All 6 data sources ingested into ChromaDB during `docker build`
- Zero startup delay — app is ready the instant the container starts

**Required Space Secrets** (Settings → Variables and secrets):

| Secret | Description |
|---|---|
| `HF_TOKEN` | HuggingFace API token (for Qwen2.5 inference) |
| `CHAINLIT_AUTH_SECRET` | JWT signing key — generate with `chainlit create-secret` |
| `ANONYMIZED_TELEMETRY` | Set to `false` to suppress ChromaDB telemetry warnings |

---

## 🛡️ Security Notes

- Passwords in `USERS` dict are demo-only — replace with a proper auth provider for production
- The `.env` file is git-ignored; never commit real credentials
- RBAC is enforced at **both** query routing **and** chunk retrieval (belt-and-suspenders)
- Off-topic guard uses semantic similarity — cannot be bypassed by prompt injection tricks
- JWT tokens expire after 15 days; `CHAINLIT_AUTH_SECRET` rotation invalidates all sessions

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **UI** | Chainlit 2.11.1 |
| **Embeddings** | sentence-transformers · all-MiniLM-L6-v2 |
| **Vector DB** | ChromaDB 0.5.3 (cosine similarity) |
| **Keyword search** | rank-bm25 |
| **LLM** | Qwen/Qwen2.5-7B-Instruct via HF Inference API |
| **PDF parsing** | pypdf |
| **Web framework** | FastAPI + uvicorn (via Chainlit) |
| **Containerisation** | Docker (python:3.11-slim) |
| **Hosting** | HuggingFace Spaces (CPU-basic) |

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
